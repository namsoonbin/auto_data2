# -*- coding: utf-8 -*-
from fastapi import APIRouter, Query, Response, HTTPException
from datetime import date, datetime
from typing import Optional
from fpdf import FPDF
import io

from services.database import get_session, SalesRecord, AdRecord
from services.calculations import calculate_fees_and_profit

router = APIRouter()


class CoupangReportPDF(FPDF):
    """Coupang Sales Report PDF Generator"""

    def __init__(self):
        super().__init__()
        self.add_page()

    def header(self):
        """PDF Header"""
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'Coupang Sales Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        """PDF Footer"""
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_summary_section(self, title: str, data: dict):
        """Add summary section"""
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, title, 0, 1)
        self.ln(2)

        self.set_font('Helvetica', '', 10)
        for key, value in data.items():
            self.cell(80, 8, key, 1)
            self.cell(0, 8, str(value), 1, 1)

        self.ln(5)

    def add_table(self, headers: list, rows: list):
        """Add data table"""
        self.set_font('Helvetica', 'B', 10)

        # Headers
        col_width = 190 / len(headers)
        for header in headers:
            self.cell(col_width, 8, header, 1, 0, 'C')
        self.ln()

        # Data rows
        self.set_font('Helvetica', '', 9)
        for row in rows:
            for item in row:
                self.cell(col_width, 8, str(item), 1, 0, 'C')
            self.ln()

        self.ln(5)


@router.get("/report/weekly")
async def generate_weekly_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    store: Optional[str] = Query(None)
):
    """Generate weekly sales report PDF"""
    db = get_session()

    try:
        # Query sales data
        sales_query = db.query(SalesRecord).filter(
            SalesRecord.date >= start_date,
            SalesRecord.date <= end_date
        )
        if store:
            sales_query = sales_query.filter(SalesRecord.store == store)

        sales_records = sales_query.all()

        if not sales_records:
            raise HTTPException(status_code=404, detail="No data found")

        # Calculate aggregates
        total_sales = 0.0
        total_quantity = 0
        total_profit = 0.0
        total_fee = 0.0
        product_data = {}

        for sale in sales_records:
            sale_amount = sale.sale_price * sale.quantity
            total_sales += sale_amount
            total_quantity += sale.quantity

            calc = calculate_fees_and_profit(
                sale_price=sale.sale_price,
                quantity=sale.quantity,
                cost_price=sale.cost_price,
                shipping_cost=sale.shipping_cost
            )

            total_profit += calc['profit']
            total_fee += calc['total_fee']

            # Product aggregation
            product_name = sale.product_name
            if product_name not in product_data:
                product_data[product_name] = {
                    'sales': 0.0,
                    'quantity': 0,
                    'profit': 0.0
                }

            product_data[product_name]['sales'] += sale_amount
            product_data[product_name]['quantity'] += sale.quantity
            product_data[product_name]['profit'] += calc['profit']

        # Calculate margin rate
        margin_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0

        # Generate PDF
        pdf = CoupangReportPDF()

        # Period info
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, f'Period: {start_date} ~ {end_date}', 0, 1)
        if store:
            pdf.cell(0, 10, f'Store: {store}', 0, 1)
        pdf.ln(5)

        # Summary metrics
        summary_data = {
            'Total Sales': f'{total_sales:,.0f} KRW',
            'Total Quantity': f'{total_quantity:,}',
            'Total Fee': f'{total_fee:,.0f} KRW',
            'Net Profit': f'{total_profit:,.0f} KRW',
            'Margin Rate': f'{margin_rate:.2f}%'
        }

        pdf.add_summary_section('Summary', summary_data)

        # Top 10 products by sales
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, 'Top 10 Products by Sales', 0, 1)
        pdf.ln(2)

        sorted_products = sorted(
            product_data.items(),
            key=lambda x: x[1]['sales'],
            reverse=True
        )[:10]

        table_headers = ['Product', 'Sales (KRW)', 'Quantity', 'Profit (KRW)']
        table_rows = [
            [
                name[:30],
                f"{data['sales']:,.0f}",
                f"{data['quantity']:,}",
                f"{data['profit']:,.0f}"
            ]
            for name, data in sorted_products
        ]

        pdf.add_table(table_headers, table_rows)

        # Output PDF
        pdf_output = pdf.output(dest='S').encode('latin1')

        filename = f"weekly_report_{start_date}_{end_date}.pdf"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }

        return Response(
            content=pdf_output,
            media_type='application/pdf',
            headers=headers
        )

    finally:
        db.close()


@router.get("/report/monthly")
async def generate_monthly_report(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    store: Optional[str] = Query(None)
):
    """Generate monthly sales report PDF"""
    from calendar import monthrange

    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    return await generate_weekly_report(start_date, end_date, store)
