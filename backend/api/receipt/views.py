from flask_restx import Resource,Namespace,fields
from flask import request
from ..services.ocr_service import OCRService
from ..services.extractor import ReceiptExtractor
from ..models.receipt import Receipt
from ..models.receipt_file import ReceiptFile
from werkzeug.datastructures import FileStorage
from datetime import datetime,timezone
import os


receipt_namespace = Namespace('receipt',description="Namespace for Reports")

upload_response_model = receipt_namespace.model(
    'UploadResponse',{
        'id':fields.Integer(),
        'file_name': fields.String,
        'message': fields.String,
    }
)

receipt_model = receipt_namespace.model(
    'Receipt',{
        'id': fields.Integer(),
        'receipt_file_id': fields.Integer,
        'purchased_at': fields.DateTime,
        'merchant_name': fields.String,
        'total_amount': fields.Float,
        'file_path': fields.String,
        'created_at': fields.DateTime,
        'updated_at': fields.DateTime,
    }
)

@receipt_namespace.route('/upload')
class UploadFile(Resource):
    @receipt_namespace.expect(receipt_namespace.parser()
            .add_argument('file',location='files', type=FileStorage,required=True)
            .add_argument('user_id',location='form',type=int,required=True))
    @receipt_namespace.marshal_with(upload_response_model)
    def post(self):
        """ post all pdf to local folder"""
        """Upload a receipt file (PDF only)"""
        args = request.args
        uploaded_file = request.files['file']
        user_id = int(request.form.get('user_id'))

        if not uploaded_file or not uploaded_file.filename.lower().endswith('.pdf'):
            receipt_file = ReceiptFile(
                user_id=user_id,
                file_name=uploaded_file.filename,
                file_path='',
                is_valid=False,
                invalid_reason="Only PDF files are allowed"
            )
            receipt_file.save()
            return {'id': receipt_file.id, 'file_name': uploaded_file.filename, 'message': 'Invalid file format (PDF only)'}, 200

        # Save the file
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, uploaded_file.filename)
        uploaded_file.save(filepath)

        # Store metadata
        receipt_file = ReceiptFile(
            user_id=user_id,
            file_name=uploaded_file.filename,
            file_path=filepath,
            is_valid=True
        )
        receipt_file.save()
        return {'id': receipt_file.id, 'file_name': uploaded_file.filename, 'message': 'Uploaded successfully'}, 201

@receipt_namespace.route('/validate')
class ValidateFile(Resource):
    @receipt_namespace.param('file_id','ReceiptFile ID',required=True)
    def post(self):
        """ Validates whether the uploaded file is a valid PDF."""
        """Validate the uploaded PDF file"""
        file_id = request.args.get('file_id', type=int)
        receipt_file = ReceiptFile.query.get_or_404(file_id)

        if not receipt_file.file_path.lower().endswith('.pdf'):
            receipt_file.is_valid = False
            receipt_file.invalid_reason = "File is not a PDF"
        else:
            receipt_file.is_valid = True
            receipt_file.invalid_reason = None

        # db.session.commit()
        return {'message': 'Validation completed', 'is_valid': receipt_file.is_valid, 'reason': receipt_file.invalid_reason}, 200

@receipt_namespace.route('/process')
class ProcessFile(Resource):
    @receipt_namespace.param('file_id','ReceiptFile ID',required=True)
    def post(self):
        """ Process Pdf for OCR data"""
        file_id = request.args.get('file_id', type=int)
        receipt_file = ReceiptFile.query.get_or_404(file_id)

        if not receipt_file.is_valid:
            return {'error': 'File is not valid for processing'}, 400
        
       # Run OCR extraction
        ocr_service = OCRService(receipt_file.file_path)
        receipt_data = ocr_service.process_receipt_pdf()

        # update version of ocr
        
        # data_extractor = ReceiptExtractor(receipt_file.file_path)
        # result = data_extractor.extract_fields(data_extractor.file_path)
        # print(result)


        # Check if a receipt already exists for this file
        existing_receipt = Receipt.query.filter_by(receipt_file_id=receipt_file.id).first()

        now = datetime.now(timezone.utc)
        new_receipt=Receipt()
        if existing_receipt:
            # Update existing receipt
            existing_receipt.merchant_name = receipt_data['merchant_name']
            existing_receipt.purchased_at = receipt_data['purchased_at']
            existing_receipt.total_amount = receipt_data['total_amount']
            existing_receipt.updated_at = now
        else:
            # Create new receipt
            new_receipt = Receipt(
                receipt_file_id=receipt_file.id,
                purchased_at=receipt_data['purchased_at'],
                merchant_name=receipt_data['merchant_name'],
                total_amount=receipt_data['total_amount'],
                file_path=receipt_file.file_path,
                created_at=now,
                updated_at=now
            )
        

        # Update processing status
        receipt_file.is_processed = True
        receipt_file.updated_at = now

        new_receipt.save()
        print()

        return {
            'message': 'Receipt processed and stored',
            'data': {
                'merchant_name': receipt_data['merchant_name'],
                'purchased_at': receipt_data['purchased_at'],
                'total_amount': receipt_data['total_amount'],
                'file_path': receipt_file.file_path
            }
        }, 201

@receipt_namespace.route('/receipts')
class ListAllReciepts(Resource):
    @receipt_namespace.marshal_list_with(receipt_model)
    def get(self):
        """Lists all receipts stored in the database"""
        return Receipt.query.all(), 200

@receipt_namespace.route('/receipts/<int:id>')
class ListReceipt(Resource):
    @receipt_namespace.marshal_with(receipt_model)
    def get(self):
        """ Retrives details of a specific receipts by its ID"""
        return Receipt.query.get_or_404(id)