# Generated migration for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_initial'),
    ]

    operations = [
        # Add indexes for Payment model
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['order'], name='finance_pay_order_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_status'], name='finance_pay_status_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_type'], name='finance_pay_type_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['order', 'payment_type'], name='finance_pay_ord_type_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['-created_at'], name='finance_pay_created_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['razorpay_order_id'], name='finance_pay_rz_ord_idx'),
        ),
        
        # Add indexes for Invoice model
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['order'], name='finance_inv_order_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['invoice_number'], name='finance_inv_number_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['-invoice_date'], name='finance_inv_date_idx'),
        ),
        
        # Add indexes for TaxConfiguration model
        migrations.AddIndex(
            model_name='taxconfiguration',
            index=models.Index(fields=['effective_from'], name='finance_tax_eff_from_idx'),
        ),
        migrations.AddIndex(
            model_name='taxconfiguration',
            index=models.Index(fields=['is_active'], name='finance_tax_active_idx'),
        ),
    ]
