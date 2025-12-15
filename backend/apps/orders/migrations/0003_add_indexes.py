# Generated migration for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_initial'),
    ]

    operations = [
        # Add indexes for Cart model
        migrations.AddIndex(
            model_name='cart',
            index=models.Index(fields=['user', 'status'], name='orders_cart_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='cart',
            index=models.Index(fields=['-created_at'], name='orders_cart_created_idx'),
        ),
        
        # Add indexes for CartItem model
        migrations.AddIndex(
            model_name='cartitem',
            index=models.Index(fields=['cart', 'variant_size'], name='orders_ci_cart_vs_idx'),
        ),
        
        # Add indexes for Order model
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['user', 'status'], name='orders_ord_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['-order_date'], name='orders_ord_date_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status', '-order_date'], name='orders_ord_status_date_idx'),
        ),
        
        # Add indexes for OrderItem model
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['order'], name='orders_oi_order_idx'),
        ),
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['variant_size'], name='orders_oi_vs_idx'),
        ),
    ]
