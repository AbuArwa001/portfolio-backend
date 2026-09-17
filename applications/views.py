from io import BytesIO
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from .models import JobApplication, CoverLetter
from .serializers import JobApplicationSerializer, CoverLetterSerializer

class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = JobApplication.objects.all()

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

        # Headers styling
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        sub_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        sub_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
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
        
        ws.append([]) # Row 2 spacer or headers
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

        # Auto fit columns
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


class CoverLetterViewSet(viewsets.ModelViewSet):
    serializer_class = CoverLetterSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = CoverLetter.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return CoverLetter.objects.all()
        return CoverLetter.objects.all()
