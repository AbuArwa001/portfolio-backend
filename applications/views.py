import csv
import datetime
import json
import os
import re
from io import BytesIO, StringIO
from django.http import HttpResponse
from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from .models import JobApplication, CoverLetter
from .serializers import JobApplicationSerializer, CoverLetterSerializer


def parse_applications_from_workbook(wb):
    """
    Intelligently parses any Excel workbook into structured JobApplication records.
    Directly supports both:
    1. Complete_Job_Application_Tracker format (Organization, Job Title, Advert Ref / Grade, Key Requirements, Key Responsibilities, Status, Shortlisted?, Closing Date, Notes)
    2. Applied Roles Tracking format (Company, Role, Status, Link, Done?, Google Search Link, Job Requirements, Date, Take By, OA, Phone Screen, Interview, Interview Done?)
    """
    results = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        if ws.max_row < 2:
            continue

        best_header_row = 1
        best_header_score = 0
        best_headers = []

        # Scan the first 10 rows to detect the true header row
        for r in range(1, min(10, ws.max_row + 1)):
            row_vals = [str(ws.cell(r, c).value or "").strip() for c in range(1, ws.max_column + 1)]
            score = 0
            for v in row_vals:
                vl = v.lower()
                if any(k in vl for k in [
                    "company", "organization", "role", "job title", "status",
                    "requirements", "responsibilities", "applied", "shortlist", "advert ref"
                ]):
                    score += 1
            if score > best_header_score:
                best_header_score = score
                best_header_row = r
                best_headers = row_vals

        if best_header_score == 0:
            continue

        col_map = {}
        for idx, h in enumerate(best_headers, 1):
            hl = h.lower()
            if any(k in hl for k in ["organization", "company", "agency", "employer", "firm"]) and "google" not in hl and "search" not in hl:
                col_map["company"] = idx
            elif any(k in hl for k in ["job title", "role", "position", "post", "designation"]):
                col_map["role"] = idx
            elif any(k in hl for k in ["advert ref", "ref / grade", "grade", "reference"]):
                col_map["advert_ref"] = idx
            elif any(k in hl for k in ["key responsibilities", "responsibilities", "jd summary"]):
                col_map["key_responsibilities"] = idx
            elif any(k in hl for k in ["key requirements", "requirements", "education & certs"]):
                col_map["job_requirements"] = idx
            elif "status" in hl or "stage" in hl:
                col_map["status"] = idx
            elif "shortlist" in hl:
                col_map["shortlisted"] = idx
            elif "closing date" in hl or "deadline" in hl:
                col_map["closing_date"] = idx
            elif any(k in hl for k in ["date of application", "date_applied", "date applied", "applied date", "date"]):
                col_map["date"] = idx
            elif any(k in hl for k in ["link", "url", "portal", "posting"]) and "google" not in hl and "search" not in hl:
                col_map["link"] = idx
            elif "google" in hl or "search" in hl:
                col_map["google_search_link"] = idx
            elif any(k in hl for k in ["done?", "done", "completed"]):
                if "interview" in hl:
                    col_map["interview_done"] = idx
                elif "done" not in col_map:
                    col_map["done"] = idx
            elif "take by" in hl or "take_by" in hl or "recruiter" in hl:
                col_map["take_by"] = idx
            elif hl == "oa" or "assessment" in hl or "test" in hl:
                col_map["oa"] = idx
            elif "phone" in hl or "screen" in hl:
                col_map["phone_screen"] = idx
            elif "interview" in hl and "done" not in hl:
                col_map["interview"] = idx
            elif any(k in hl for k in ["notes", "comment", "remark", "salary"]):
                col_map["notes"] = idx

        for r in range(best_header_row + 1, ws.max_row + 1):
            comp_idx = col_map.get("company")
            comp = ws.cell(r, comp_idx).value if comp_idx else None
            if not comp or not str(comp).strip():
                continue

            comp_clean = str(comp).strip().replace("\n", " ")

            # Role / Job Title
            role_idx = col_map.get("role")
            role_val = ws.cell(r, role_idx).value if role_idx else None
            role_clean = str(role_val).strip() if role_val else "Network / Software Engineer"

            # Advert Ref / Grade
            advert_ref = str(ws.cell(r, col_map["advert_ref"]).value or "").strip() if "advert_ref" in col_map else ""

            # Key Responsibilities & Requirements
            key_resp = str(ws.cell(r, col_map["key_responsibilities"]).value or "").strip() if "key_responsibilities" in col_map else ""
            job_req = str(ws.cell(r, col_map["job_requirements"]).value or "").strip() if "job_requirements" in col_map else ""

            # Status Normalization
            stat_idx = col_map.get("status")
            raw_stat = str(ws.cell(r, stat_idx).value or "").strip() if stat_idx else ""
            status_val = "Applied"
            raw_stat_lower = raw_stat.lower()
            if any(k in raw_stat_lower for k in ["interview", "shortlist", "assessment", "round"]):
                status_val = "Interviewing"
            elif "offer" in raw_stat_lower:
                status_val = "Offer"
            elif any(k in raw_stat_lower for k in ["reject", "declined", "closed", "unsuccessful"]):
                status_val = "Rejected"
            elif any(k in raw_stat_lower for k in ["to apply", "not yet", "pending", "draft", "wishlist"]):
                status_val = "Not yet Applied"
            elif "applied" in raw_stat_lower:
                status_val = "Applied"

            # Shortlisted / Interview flags
            shortlisted_idx = col_map.get("shortlisted")
            raw_short = str(ws.cell(r, shortlisted_idx).value or "").strip().upper() if shortlisted_idx else ""
            shortlisted = raw_short in ["YES", "TRUE", "1", "SHORTLISTED"]
            if shortlisted and status_val == "Applied":
                status_val = "Interviewing"

            # Date Applied & Closing Date Normalization
            date_idx = col_map.get("date")
            raw_date = ws.cell(r, date_idx).value if date_idx else None
            date_applied = None
            if isinstance(raw_date, (datetime.date, datetime.datetime)):
                date_applied = raw_date.strftime("%Y-%m-%d")
            elif isinstance(raw_date, str) and raw_date.strip() and raw_date.strip().upper() not in ["N/A", "NONE", ""]:
                for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                    try:
                        date_applied = datetime.datetime.strptime(raw_date.strip(), fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        pass
            if not date_applied:
                date_applied = datetime.date.today().strftime("%Y-%m-%d")

            closing_idx = col_map.get("closing_date")
            raw_closing = ws.cell(r, closing_idx).value if closing_idx else None
            closing_date = None
            if isinstance(raw_closing, (datetime.date, datetime.datetime)):
                closing_date = raw_closing.strftime("%Y-%m-%d")
            elif isinstance(raw_closing, str) and raw_closing.strip() and raw_closing.strip().upper() not in ["N/A", "NONE", ""]:
                for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                    try:
                        closing_date = datetime.datetime.strptime(raw_closing.strip(), fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        pass

            done_idx = col_map.get("done")
            raw_done = str(ws.cell(r, done_idx).value or "").strip().upper() if done_idx else ""
            done = raw_done in ["YES", "TRUE", "1"]

            int_done_idx = col_map.get("interview_done")
            raw_int_done = str(ws.cell(r, int_done_idx).value or "").strip().upper() if int_done_idx else ""
            interview_done = raw_int_done in ["YES", "TRUE", "1"]

            oa_idx = col_map.get("oa")
            raw_oa = str(ws.cell(r, oa_idx).value or "").strip().upper() if oa_idx else ""
            oa = raw_oa in ["YES", "TRUE", "1"]

            phone_idx = col_map.get("phone_screen")
            raw_phone = str(ws.cell(r, phone_idx).value or "").strip().upper() if phone_idx else ""
            phone_screen = raw_phone in ["YES", "TRUE", "1"]

            # Links
            link_idx = col_map.get("link")
            link = str(ws.cell(r, link_idx).value or "").strip() if link_idx else ""
            if link and not link.startswith("http"):
                link = "https://" + link if "." in link else ""

            g_idx = col_map.get("google_search_link")
            google_search_link = str(ws.cell(r, g_idx).value or "").strip() if g_idx else ""

            take_by_idx = col_map.get("take_by")
            take_by = str(ws.cell(r, take_by_idx).value or "").strip() if take_by_idx else ""

            # Notes
            notes_val = str(ws.cell(r, col_map["notes"]).value or "").strip() if "notes" in col_map else ""

            results.append({
                "company": comp_clean,
                "organization": comp_clean,
                "role": role_clean,
                "job_title": role_clean,
                "status": status_val,
                "link": link,
                "done": done,
                "google_search_link": google_search_link,
                "job_requirements": job_req,
                "key_responsibilities": key_resp,
                "advert_ref": advert_ref,
                "date_applied": date_applied,
                "closing_date": closing_date,
                "take_by": take_by,
                "oa": oa,
                "phone_screen": phone_screen,
                "interview": shortlisted or (status_val == "Interviewing"),
                "shortlisted": shortlisted,
                "interview_done": interview_done,
                "notes": notes_val,
            })
    return results


def parse_applications_from_csv(csv_text):
    """
    Parses CSV text into structured JobApplication records.
    """
    f = StringIO(csv_text.strip())
    reader = csv.reader(f)
    rows = [r for r in reader if any(field.strip() for field in r)]
    if not rows or len(rows) < 2:
        return []

    # Detect header row among first 5 rows
    best_header_row = 0
    best_header_score = 0
    for idx, r in enumerate(rows[:5]):
        score = sum(1 for v in r if any(k in v.lower() for k in [
            "company", "organization", "role", "job title", "status", "link", "date", "advert ref"
        ]))
        if score > best_header_score:
            best_header_score = score
            best_header_row = idx

    headers = [h.strip() for h in rows[best_header_row]]
    col_map = {}
    for idx, h in enumerate(headers):
        hl = h.lower()
        if any(k in hl for k in ["organization", "company", "agency", "employer", "firm"]) and "google" not in hl:
            col_map["company"] = idx
        elif any(k in hl for k in ["job title", "role", "position", "post"]):
            col_map["role"] = idx
        elif any(k in hl for k in ["advert ref", "ref / grade", "grade"]):
            col_map["advert_ref"] = idx
        elif any(k in hl for k in ["key responsibilities", "responsibilities"]):
            col_map["key_responsibilities"] = idx
        elif any(k in hl for k in ["key requirements", "requirements"]):
            col_map["job_requirements"] = idx
        elif "status" in hl:
            col_map["status"] = idx
        elif "shortlist" in hl:
            col_map["shortlisted"] = idx
        elif any(k in hl for k in ["link", "url", "portal"]) and "google" not in hl:
            col_map["link"] = idx
        elif "google" in hl:
            col_map["google_search_link"] = idx
        elif "closing date" in hl:
            col_map["closing_date"] = idx
        elif "date" in hl:
            col_map["date"] = idx
        elif any(k in hl for k in ["note", "comment", "ref"]):
            col_map["notes"] = idx

    results = []
    for r in rows[best_header_row + 1:]:
        comp_idx = col_map.get("company", 0)
        if comp_idx >= len(r) or not r[comp_idx].strip():
            continue
        comp = r[comp_idx].strip()
        role = r[col_map.get("role", 1)].strip() if col_map.get("role") and col_map["role"] < len(r) else "Network / Software Engineer"
        status_val = r[col_map.get("status")].strip() if col_map.get("status") and col_map["status"] < len(r) else "Applied"
        link = r[col_map.get("link")].strip() if col_map.get("link") and col_map["link"] < len(r) else ""
        date_str = r[col_map.get("date")].strip() if col_map.get("date") and col_map["date"] < len(r) else datetime.date.today().strftime("%Y-%m-%d")
        reqs = r[col_map.get("job_requirements")].strip() if col_map.get("job_requirements") and col_map["job_requirements"] < len(r) else ""
        resp = r[col_map.get("key_responsibilities")].strip() if col_map.get("key_responsibilities") and col_map["key_responsibilities"] < len(r) else ""
        advert = r[col_map.get("advert_ref")].strip() if col_map.get("advert_ref") and col_map["advert_ref"] < len(r) else ""
        notes = r[col_map.get("notes")].strip() if col_map.get("notes") and col_map["notes"] < len(r) else ""

        shortlisted = False
        if col_map.get("shortlisted") and col_map["shortlisted"] < len(r):
            shortlisted = r[col_map["shortlisted"]].strip().upper() in ["YES", "TRUE", "1"]

        results.append({
            "company": comp,
            "organization": comp,
            "role": role or "Network / Software Engineer",
            "job_title": role or "Network / Software Engineer",
            "status": status_val or "Applied",
            "link": link,
            "done": False,
            "google_search_link": "",
            "job_requirements": reqs,
            "key_responsibilities": resp,
            "advert_ref": advert,
            "date_applied": date_str or datetime.date.today().strftime("%Y-%m-%d"),
            "take_by": "",
            "oa": False,
            "phone_screen": False,
            "interview": shortlisted or ("interview" in status_val.lower()),
            "shortlisted": shortlisted,
            "interview_done": False,
            "notes": notes,
        })
    return results


class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = JobApplication.objects.all()

    def get_permissions(self):
        if self.action in ["import_file", "bulk_create"]:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return JobApplication.objects.all()
        return JobApplication.objects.all()

    @action(detail=False, methods=["get"], url_path="export-excel")
    def export_excel(self, request):
        """
        Exports all applications formatted exactly matching Complete_Job_Application_Tracker.xlsx
        (Detailed Job Tracker sheet) as well as the Applied Roles Tracking sheet.
        """
        applications = self.get_queryset()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Detailed Job Tracker"

        # Sheet 1: Detailed Job Tracker format (Complete_Job_Application_Tracker)
        headers_detailed = [
            "Organization", "Job Title", "Advert Ref / Grade",
            "Key Requirements (Education & Certs)", "Key Responsibilities (JD Summary)",
            "Status", "Shortlisted?", "Closing Date", "Notes"
        ]

        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        for col_idx, h in enumerate(headers_detailed, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="left", vertical="center")

        for app in applications:
            shortlisted_str = "YES" if (app.shortlisted or app.interview) else "No"
            closing_str = ""
            if app.closing_date:
                closing_str = app.closing_date.strftime("%d/%m/%Y")
            elif app.date_applied:
                closing_str = app.date_applied.strftime("%d/%m/%Y")
            else:
                closing_str = "N/A"

            ws.append([
                app.company,
                app.role,
                app.advert_ref or "N/A",
                app.job_requirements,
                app.key_responsibilities,
                app.status,
                shortlisted_str,
                closing_str,
                app.notes,
            ])

        # Auto-fit sheet 1 columns
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) if len(col) > 0 else 15
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 50)

        # Sheet 2: Applied Roles Tracking Format
        ws2 = wb.create_sheet(title="Applied Roles Tracking")
        headers_applied = [
            "Company", "Role", "Status", "Link", "Done?", 
            "Google Search Link", "Job Requirements", "Date of Application",
            "Take By", "OA", "Phone Screen", "Interview", "Interview Done?"
        ]
        for col_idx, h in enumerate(headers_applied, 1):
            cell = ws2.cell(row=1, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="left", vertical="center")

        for app in applications:
            ws2.append([
                app.company,
                app.role,
                app.status,
                app.link,
                "YES" if app.done else "NO",
                app.google_search_link,
                app.job_requirements,
                app.date_applied.strftime("%Y-%m-%d") if app.date_applied else "",
                app.take_by,
                "YES" if app.oa else "NO",
                "YES" if app.phone_screen else "NO",
                "YES" if (app.interview or app.shortlisted) else "NO",
                "YES" if app.interview_done else "NO",
            ])

        for col in ws2.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) if len(col) > 0 else 15
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws2.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 45)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="Complete_Job_Application_Tracker.xlsx"'
        return response

    @action(detail=False, methods=["post"], url_path="import-file", permission_classes=[permissions.AllowAny], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def import_file(self, request):
        """
        Imports applications from an uploaded file (.xlsx, .xls, .csv, .json)
        or predefined local spreadsheet templates.
        Supports dry_run=true for live previewing before database commit.
        """
        uploaded_file = request.FILES.get("file")
        source_key = request.data.get("source_file")
        dry_run = str(request.query_params.get("dry_run", request.data.get("dry_run", "false"))).lower() in ["true", "1"]
        skip_duplicates = str(request.data.get("skip_duplicates", "true")).lower() in ["true", "1"]

        parsed_items = []

        try:
            # 1. Check if uploaded file
            if uploaded_file:
                fname = uploaded_file.name.lower()
                if fname.endswith((".xlsx", ".xls")):
                    wb = openpyxl.load_workbook(uploaded_file, data_only=True)
                    parsed_items = parse_applications_from_workbook(wb)
                elif fname.endswith((".csv", ".tsv")):
                    content = uploaded_file.read().decode("utf-8-sig", errors="ignore")
                    parsed_items = parse_applications_from_csv(content)
                elif fname.endswith(".json"):
                    data = json.loads(uploaded_file.read().decode("utf-8"))
                    parsed_items = data if isinstance(data, list) else data.get("applications", [])
                else:
                    return Response({"error": "Unsupported file format. Please upload .xlsx, .xls, .csv, or .json."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Check if local template requested
            elif source_key:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                file_map = {
                    "complete_tracker": os.path.join(base_dir, "Complete_Job_Application_Tracker (1).xlsx"),
                    "applied_roles": os.path.join(base_dir, "Applied Roles - Tracking Spreadsheet .xlsx"),
                }
                target_path = file_map.get(source_key, source_key)
                if not os.path.exists(target_path):
                    desktop_path = f"/home/khalfan/Desktop/portfolio-backend/{source_key}"
                    if os.path.exists(desktop_path):
                        target_path = desktop_path

                if os.path.exists(target_path):
                    wb = openpyxl.load_workbook(target_path, data_only=True)
                    parsed_items = parse_applications_from_workbook(wb)
                else:
                    return Response({"error": f"File '{source_key}' not found on server."}, status=status.HTTP_404_NOT_FOUND)

            # 3. Direct JSON payload
            elif "applications" in request.data:
                parsed_items = request.data.get("applications", [])

            else:
                return Response({"error": "No file, source_file, or applications payload provided."}, status=status.HTTP_400_BAD_REQUEST)

            if not parsed_items:
                return Response({"error": "No valid application records could be detected in the provided file."}, status=status.HTTP_400_BAD_REQUEST)

            # If Dry Run, return records for preview without saving to database
            if dry_run:
                return Response({
                    "preview": True,
                    "count": len(parsed_items),
                    "items": parsed_items,
                    "message": f"Successfully parsed {len(parsed_items)} records ready for review.",
                }, status=status.HTTP_200_OK)

            # Save to Database
            user = request.user if request.user.is_authenticated else None
            created_records = []
            skipped_records = []

            with transaction.atomic():
                for item in parsed_items:
                    company = (item.get("company") or item.get("organization") or "").strip()
                    role = (item.get("role") or item.get("job_title") or "").strip()
                    if not company:
                        continue

                    # Duplicate check
                    if skip_duplicates and JobApplication.objects.filter(company__iexact=company, role__iexact=role).exists():
                        skipped_records.append({"company": company, "role": role, "reason": "Already exists in database"})
                        continue

                    shortlisted = bool(item.get("shortlisted", False) or item.get("interview", False))
                    status_val = item.get("status", "Applied")
                    if shortlisted and status_val == "Applied":
                        status_val = "Interviewing"

                    obj = JobApplication.objects.create(
                        user=user,
                        company=company,
                        role=role or "Network / Software Engineer",
                        status=status_val,
                        link=item.get("link", ""),
                        done=bool(item.get("done", False)),
                        google_search_link=item.get("google_search_link", ""),
                        job_requirements=item.get("job_requirements", ""),
                        key_responsibilities=item.get("key_responsibilities", ""),
                        advert_ref=item.get("advert_ref", ""),
                        date_applied=item.get("date_applied") or datetime.date.today(),
                        closing_date=item.get("closing_date"),
                        take_by=item.get("take_by", ""),
                        oa=bool(item.get("oa", False)),
                        phone_screen=bool(item.get("phone_screen", False)),
                        interview=shortlisted,
                        shortlisted=shortlisted,
                        interview_done=bool(item.get("interview_done", False)),
                        notes=item.get("notes", ""),
                    )
                    created_records.append(obj)

            return Response({
                "success": True,
                "count": len(created_records),
                "skipped_count": len(skipped_records),
                "message": f"Successfully imported {len(created_records)} job applications into your tracker.",
                "items": JobApplicationSerializer(created_records, many=True).data,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Failed to import file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="bulk-create", permission_classes=[permissions.AllowAny], parser_classes=[JSONParser])
    def bulk_create(self, request):
        """
        Creates multiple application records from JSON array with full Complete_Job_Application_Tracker support.
        """
        items = request.data.get("applications", [])
        skip_duplicates = str(request.data.get("skip_duplicates", "true")).lower() in ["true", "1"]

        if not isinstance(items, list) or not items:
            return Response({"error": "Expected a list of application items in 'applications'."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user if request.user.is_authenticated else None
        created_records = []
        skipped_records = []

        try:
            with transaction.atomic():
                for item in items:
                    company = (item.get("company") or item.get("organization") or "").strip()
                    role = (item.get("role") or item.get("job_title") or "").strip()
                    if not company:
                        continue

                    if skip_duplicates and JobApplication.objects.filter(company__iexact=company, role__iexact=role).exists():
                        skipped_records.append({"company": company, "role": role})
                        continue

                    shortlisted = bool(item.get("shortlisted", False) or item.get("interview", False))
                    status_val = item.get("status", "Applied")
                    if shortlisted and status_val == "Applied":
                        status_val = "Interviewing"

                    obj = JobApplication.objects.create(
                        user=user,
                        company=company,
                        role=role or "Network / Software Engineer",
                        status=status_val,
                        link=item.get("link", ""),
                        done=bool(item.get("done", False)),
                        google_search_link=item.get("google_search_link", ""),
                        job_requirements=item.get("job_requirements", ""),
                        key_responsibilities=item.get("key_responsibilities", ""),
                        advert_ref=item.get("advert_ref", ""),
                        date_applied=item.get("date_applied") or datetime.date.today(),
                        closing_date=item.get("closing_date"),
                        take_by=item.get("take_by", ""),
                        oa=bool(item.get("oa", False)),
                        phone_screen=bool(item.get("phone_screen", False)),
                        interview=shortlisted,
                        shortlisted=shortlisted,
                        interview_done=bool(item.get("interview_done", False)),
                        notes=item.get("notes", ""),
                    )
                    created_records.append(obj)

            return Response({
                "success": True,
                "count": len(created_records),
                "skipped_count": len(skipped_records),
                "message": f"Successfully created {len(created_records)} applications.",
                "items": JobApplicationSerializer(created_records, many=True).data,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Bulk creation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CoverLetterViewSet(viewsets.ModelViewSet):
    serializer_class = CoverLetterSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = CoverLetter.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return CoverLetter.objects.all()
        return CoverLetter.objects.all()
