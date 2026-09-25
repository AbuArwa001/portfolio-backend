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
    Detects dynamic header rows, column synonyms, multi-field requirement combinations,
    and formats dates and boolean fields.
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
                    "requirements", "responsibilities", "applied", "shortlist", "interview"
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
            elif "status" in hl or "stage" in hl:
                col_map["status"] = idx
            elif "shortlist" in hl:
                col_map["shortlisted"] = idx
            elif any(k in hl for k in ["link", "url", "portal", "posting"]) and "google" not in hl and "search" not in hl:
                col_map["link"] = idx
            elif "google" in hl or "search" in hl:
                col_map["google_search_link"] = idx
            elif any(k in hl for k in ["done?", "done", "completed"]):
                if "interview" in hl:
                    col_map["interview_done"] = idx
                elif "done" not in col_map:
                    col_map["done"] = idx
            elif any(k in hl for k in ["requirement", "responsibilit", "description", "jd"]):
                if "job_requirements" not in col_map:
                    col_map["job_requirements"] = []
                col_map["job_requirements"].append((h, idx))
            elif any(k in hl for k in ["date of application", "date_applied", "date applied", "applied date", "closing date", "date"]):
                if "date" not in col_map:
                    col_map["date"] = idx
            elif "take by" in hl or "take_by" in hl or "recruiter" in hl:
                col_map["take_by"] = idx
            elif hl == "oa" or "assessment" in hl or "test" in hl:
                col_map["oa"] = idx
            elif "phone" in hl or "screen" in hl:
                col_map["phone_screen"] = idx
            elif "interview" in hl and "done" not in hl:
                col_map["interview"] = idx
            elif any(k in hl for k in ["notes", "ref", "grade", "comment", "remark", "salary"]):
                if "notes" not in col_map:
                    col_map["notes"] = []
                col_map["notes"].append((h, idx))

        for r in range(best_header_row + 1, ws.max_row + 1):
            comp_idx = col_map.get("company")
            comp = ws.cell(r, comp_idx).value if comp_idx else None
            if not comp or not str(comp).strip():
                continue

            comp_clean = str(comp).strip().replace("\n", " ")

            # Role
            role_idx = col_map.get("role")
            role_val = ws.cell(r, role_idx).value if role_idx else None
            role_clean = str(role_val).strip() if role_val else "Network / Software Engineer"

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

            # Date Normalization
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

            # Shortlisted / Interview flags
            shortlisted_idx = col_map.get("shortlisted")
            raw_short = str(ws.cell(r, shortlisted_idx).value or "").strip().upper() if shortlisted_idx else ""
            interview = raw_short in ["YES", "TRUE", "1", "SHORTLISTED"]
            if interview and status_val == "Applied":
                status_val = "Interviewing"

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

            # Requirements
            req_parts = []
            if "job_requirements" in col_map:
                for h_name, c_idx in col_map["job_requirements"]:
                    val = str(ws.cell(r, c_idx).value or "").strip()
                    if val:
                        req_parts.append(f"{h_name}: {val}")
            job_requirements = "\n\n".join(req_parts)

            # Notes
            note_parts = []
            if "notes" in col_map:
                for h_name, c_idx in col_map["notes"]:
                    val = str(ws.cell(r, c_idx).value or "").strip()
                    if val:
                        note_parts.append(f"{h_name}: {val}")
            notes = "\n".join(note_parts)

            results.append({
                "company": comp_clean,
                "role": role_clean,
                "status": status_val,
                "link": link,
                "done": done,
                "google_search_link": google_search_link,
                "job_requirements": job_requirements,
                "date_applied": date_applied,
                "take_by": take_by,
                "oa": oa,
                "phone_screen": phone_screen,
                "interview": interview,
                "interview_done": interview_done,
                "notes": notes,
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
            "company", "organization", "role", "job title", "status", "link", "date"
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
        elif "status" in hl:
            col_map["status"] = idx
        elif any(k in hl for k in ["link", "url", "portal"]) and "google" not in hl:
            col_map["link"] = idx
        elif "google" in hl:
            col_map["google_search_link"] = idx
        elif "date" in hl:
            col_map["date"] = idx
        elif any(k in hl for k in ["requirement", "responsibilit", "description"]):
            col_map["job_requirements"] = idx
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
        notes = r[col_map.get("notes")].strip() if col_map.get("notes") and col_map["notes"] < len(r) else ""

        results.append({
            "company": comp,
            "role": role or "Network / Software Engineer",
            "status": status_val or "Applied",
            "link": link,
            "done": False,
            "google_search_link": "",
            "job_requirements": reqs,
            "date_applied": date_str or datetime.date.today().strftime("%Y-%m-%d"),
            "take_by": "",
            "oa": False,
            "phone_screen": False,
            "interview": "interview" in status_val.lower(),
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
        applications = self.get_queryset()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Applied Roles Tracking"

        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        center_align = Alignment(horizontal="center", vertical="center")

        # Row 1: Title
        ws.merge_cells("A1:M1")
        title_cell = ws["A1"]
        title_cell.value = "KHALFAN ATHMAN - APPLIED ROLES TRACKING SPREADSHEET"
        title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        title_cell.alignment = center_align

        # Row 2: Headers
        headers = [
            "Company", "Role", "Status", "Link", "Done?", 
            "Google Search Link", "Job Requirements", "Date of Application",
            "Take By", "OA", "Phone Screen", "Interview", "Interview Done?"
        ]
        
        ws.append([])
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=2, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="left", vertical="center")

        # Data rows
        for app in applications:
            ws.append([
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
                "YES" if app.interview else "NO",
                "YES" if app.interview_done else "NO",
            ])

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col[1:]) if len(col) > 1 else 15
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 45)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="Applied_Roles_Tracking.xlsx"'
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
                # Common local files
                file_map = {
                    "complete_tracker": os.path.join(base_dir, "Complete_Job_Application_Tracker (1).xlsx"),
                    "applied_roles": os.path.join(base_dir, "Applied Roles - Tracking Spreadsheet .xlsx"),
                }
                target_path = file_map.get(source_key, source_key)
                if not os.path.exists(target_path):
                    # Check desktop
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
                    company = (item.get("company") or "").strip()
                    role = (item.get("role") or "").strip()
                    if not company:
                        continue

                    # Duplicate check
                    if skip_duplicates and JobApplication.objects.filter(company__iexact=company, role__iexact=role).exists():
                        skipped_records.append({"company": company, "role": role, "reason": "Already exists in database"})
                        continue

                    obj = JobApplication.objects.create(
                        user=user,
                        company=company,
                        role=role or "Network / Software Engineer",
                        status=item.get("status", "Applied"),
                        link=item.get("link", ""),
                        done=bool(item.get("done", False)),
                        google_search_link=item.get("google_search_link", ""),
                        job_requirements=item.get("job_requirements", ""),
                        date_applied=item.get("date_applied") or datetime.date.today(),
                        take_by=item.get("take_by", ""),
                        oa=bool(item.get("oa", False)),
                        phone_screen=bool(item.get("phone_screen", False)),
                        interview=bool(item.get("interview", False)),
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
        Creates multiple application records from JSON array.
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
                    company = (item.get("company") or "").strip()
                    role = (item.get("role") or "").strip()
                    if not company:
                        continue

                    if skip_duplicates and JobApplication.objects.filter(company__iexact=company, role__iexact=role).exists():
                        skipped_records.append({"company": company, "role": role})
                        continue

                    obj = JobApplication.objects.create(
                        user=user,
                        company=company,
                        role=role or "Network / Software Engineer",
                        status=item.get("status", "Applied"),
                        link=item.get("link", ""),
                        done=bool(item.get("done", False)),
                        google_search_link=item.get("google_search_link", ""),
                        job_requirements=item.get("job_requirements", ""),
                        date_applied=item.get("date_applied") or datetime.date.today(),
                        take_by=item.get("take_by", ""),
                        oa=bool(item.get("oa", False)),
                        phone_screen=bool(item.get("phone_screen", False)),
                        interview=bool(item.get("interview", False)),
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
