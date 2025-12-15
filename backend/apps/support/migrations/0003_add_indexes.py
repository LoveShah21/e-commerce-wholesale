# Generated migration for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0002_initial'),
    ]

    operations = [
        # Add indexes for Inquiry model
        migrations.AddIndex(
            model_name='inquiry',
            index=models.Index(fields=['user', 'status'], name='support_inq_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='inquiry',
            index=models.Index(fields=['-inquiry_date'], name='support_inq_date_idx'),
        ),
        migrations.AddIndex(
            model_name='inquiry',
            index=models.Index(fields=['status'], name='support_inq_status_idx'),
        ),
        
        # Add indexes for QuotationRequest model
        migrations.AddIndex(
            model_name='quotationrequest',
            index=models.Index(fields=['inquiry'], name='support_qr_inquiry_idx'),
        ),
        migrations.AddIndex(
            model_name='quotationrequest',
            index=models.Index(fields=['status'], name='support_qr_status_idx'),
        ),
        
        # Add indexes for QuotationPrice model
        migrations.AddIndex(
            model_name='quotationprice',
            index=models.Index(fields=['quotation'], name='support_qp_quot_idx'),
        ),
        migrations.AddIndex(
            model_name='quotationprice',
            index=models.Index(fields=['status'], name='support_qp_status_idx'),
        ),
        migrations.AddIndex(
            model_name='quotationprice',
            index=models.Index(fields=['valid_until'], name='support_qp_valid_idx'),
        ),
        
        # Add indexes for Complaint model
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['user', 'status'], name='support_cmp_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['-complaint_date'], name='support_cmp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['status'], name='support_cmp_status_idx'),
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['complaint_category'], name='support_cmp_category_idx'),
        ),
        
        # Add indexes for Feedback model
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['user'], name='support_fb_user_idx'),
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['order'], name='support_fb_order_idx'),
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['-feedback_date'], name='support_fb_date_idx'),
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['rating'], name='support_fb_rating_idx'),
        ),
    ]
