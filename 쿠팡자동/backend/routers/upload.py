# -*- coding: utf-8 -*-
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from typing import Optional
from datetime import datetime
from models.schemas import UploadResponse, IntegratedUploadResponse
from services import parser
from services.integrated_parser import parse_integrated_files
from services.database import get_db
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user, get_current_tenant
from models.auth import User, Tenant

router = APIRouter()


@router.post("/upload/sales", response_model=UploadResponse)
async def upload_sales_file(file: UploadFile = File(...)):
    """Upload sales data Excel file"""
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["xlsx", "xls", "csv"]:
        return UploadResponse(
            status="error",
            message="Unsupported file format. Only xlsx, xls, csv allowed",
            records=0,
            errors=["Unsupported file format"]
        )

    try:
        data = await parser.parse_sales_file(file)
        return UploadResponse(
            status="success",
            message=f"Successfully uploaded {len(data)} sales records",
            records=len(data),
            errors=[]
        )
    except Exception as e:
        return UploadResponse(
            status="error",
            message=f"File processing error: {str(e)}",
            records=0,
            errors=[str(e)]
        )


@router.post("/upload/ads", response_model=UploadResponse)
async def upload_ads_file(file: UploadFile = File(...)):
    """Upload advertising data Excel file"""
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["xlsx", "xls", "csv"]:
        return UploadResponse(
            status="error",
            message="Unsupported file format. Only xlsx, xls, csv allowed",
            records=0,
            errors=["Unsupported file format"]
        )

    try:
        data = await parser.parse_ads_file(file)
        return UploadResponse(
            status="success",
            message=f"Successfully uploaded {len(data)} ad records",
            records=len(data),
            errors=[]
        )
    except Exception as e:
        return UploadResponse(
            status="error",
            message=f"File processing error: {str(e)}",
            records=0,
            errors=[str(e)]
        )


@router.post("/upload/products", response_model=UploadResponse)
async def upload_product_master_file(file: UploadFile = File(...)):
    """Upload product master data Excel file"""
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["xlsx", "xls", "csv"]:
        return UploadResponse(
            status="error",
            message="Unsupported file format. Only xlsx, xls, csv allowed",
            records=0,
            errors=["Unsupported file format"]
        )

    try:
        data = await parser.parse_product_master_file(file)
        return UploadResponse(
            status="success",
            message=f"Successfully uploaded {len(data)} product records",
            records=len(data),
            errors=[]
        )
    except Exception as e:
        return UploadResponse(
            status="error",
            message=f"File processing error: {str(e)}",
            records=0,
            errors=[str(e)]
        )


@router.post("/upload/integrated", response_model=IntegratedUploadResponse)
async def upload_integrated_files(
    sales_file: UploadFile = File(..., description="Sales data Excel file"),
    ads_file: UploadFile = File(..., description="Advertising data Excel file"),
    data_date: Optional[str] = Form(None, description="Data date (YYYY-MM-DD format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Upload and integrate 2 Excel files: sales and ads (margin data loaded from database)

    This endpoint processes 2 files and merges them with margin data from ProductMargin table.

    Returns statistics about:
    - Total records processed
    - Records matched with advertising data
    - Records matched with margin data (from database)
    - Fully integrated records
    """
    # Validate file formats
    for file, name in [(sales_file, "Sales"), (ads_file, "Ads")]:
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["xlsx", "xls"]:
            return IntegratedUploadResponse(
                status="error",
                message=f"{name} file: Unsupported format. Only xlsx, xls allowed",
                total_records=0,
                matched_with_ads=0,
                matched_with_margin=0,
                fully_integrated=0,
                warnings=[f"{name} file format error"]
            )

    # Parse data_date if provided
    date_obj = None
    if data_date:
        try:
            date_obj = datetime.strptime(data_date, "%Y-%m-%d").date()
        except ValueError:
            return IntegratedUploadResponse(
                status="error",
                message="Invalid date format. Use YYYY-MM-DD",
                total_records=0,
                matched_with_ads=0,
                matched_with_margin=0,
                fully_integrated=0,
                warnings=["Date format error"]
            )

    try:
        # Process 2 files (margin data loaded from database)
        total_records, matched_ads, matched_margin, warnings = await parse_integrated_files(
            sales_file.file,
            ads_file.file,
            db,
            current_tenant.id,
            date_obj
        )

        # Calculate fully integrated records (records with both ads AND margin data)
        # We can query the database for this tenant
        from services.database import IntegratedRecord, UploadHistory
        fully_integrated = db.query(IntegratedRecord).filter(
            IntegratedRecord.tenant_id == current_tenant.id,
            IntegratedRecord.ad_cost > 0,
            IntegratedRecord.cost_price > 0
        ).count()

        # Save upload history
        upload_history = UploadHistory(
            tenant_id=current_tenant.id,
            sales_filename=sales_file.filename,
            ads_filename=ads_file.filename,
            margin_filename="DB 자동 조회",
            data_date=date_obj,
            total_records=total_records,
            matched_with_ads=matched_ads,
            matched_with_margin=matched_margin,
            fully_integrated=fully_integrated,
            status='success'
        )
        db.add(upload_history)
        db.commit()

        return IntegratedUploadResponse(
            status="success",
            message=f"Successfully processed and integrated {total_records} records",
            total_records=total_records,
            matched_with_ads=matched_ads,
            matched_with_margin=matched_margin,
            fully_integrated=fully_integrated,
            warnings=warnings
        )

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Integration error: {error_detail}")

        # Save failed upload history
        from services.database import UploadHistory
        try:
            upload_history = UploadHistory(
                tenant_id=current_tenant.id,
                sales_filename=sales_file.filename,
                ads_filename=ads_file.filename,
                margin_filename="DB 자동 조회",
                data_date=date_obj,
                total_records=0,
                matched_with_ads=0,
                matched_with_margin=0,
                fully_integrated=0,
                status='error',
                error_message=str(e)
            )
            db.add(upload_history)
            db.commit()
        except Exception as hist_err:
            print(f"Failed to save upload history: {hist_err}")

        return IntegratedUploadResponse(
            status="error",
            message=f"File integration error: {str(e)}",
            total_records=0,
            matched_with_ads=0,
            matched_with_margin=0,
            fully_integrated=0,
            warnings=[str(e)]
        )


@router.get("/upload/history")
async def get_upload_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get upload history records for current tenant"""
    from services.database import UploadHistory

    uploads = db.query(UploadHistory).filter(
        UploadHistory.tenant_id == current_tenant.id
    ).order_by(UploadHistory.uploaded_at.desc()).all()

    return {
        "uploads": [
            {
                "id": upload.id,
                "uploaded_at": upload.uploaded_at.isoformat(),
                "sales_filename": upload.sales_filename,
                "ads_filename": upload.ads_filename,
                "margin_filename": upload.margin_filename,
                "data_date": upload.data_date.isoformat() if upload.data_date else None,
                "total_records": upload.total_records,
                "matched_with_ads": upload.matched_with_ads,
                "matched_with_margin": upload.matched_with_margin,
                "fully_integrated": upload.fully_integrated,
                "status": upload.status,
                "error_message": upload.error_message
            }
            for upload in uploads
        ],
        "count": len(uploads)
    }


@router.delete("/upload/history/{upload_id}")
async def delete_upload_history(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Delete a specific upload history record for current tenant"""
    from services.database import UploadHistory

    upload = db.query(UploadHistory).filter(
        UploadHistory.id == upload_id,
        UploadHistory.tenant_id == current_tenant.id
    ).first()

    if not upload:
        raise HTTPException(status_code=404, detail="Upload history not found")

    db.delete(upload)
    db.commit()

    return {"message": "Upload history deleted successfully"}
