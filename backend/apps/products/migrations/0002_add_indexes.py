# Generated migration for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        # Add indexes for Product model
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['-created_at'], name='products_pr_created_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['product_name'], name='products_pr_name_idx'),
        ),
        
        # Add indexes for ProductVariant model
        migrations.AddIndex(
            model_name='productvariant',
            index=models.Index(fields=['product', 'fabric', 'color'], name='products_pv_prod_fab_col_idx'),
        ),
        migrations.AddIndex(
            model_name='productvariant',
            index=models.Index(fields=['sku'], name='products_pv_sku_idx'),
        ),
        migrations.AddIndex(
            model_name='productvariant',
            index=models.Index(fields=['-created_at'], name='products_pv_created_idx'),
        ),
        
        # Add indexes for VariantSize model
        migrations.AddIndex(
            model_name='variantsize',
            index=models.Index(fields=['variant', 'size'], name='products_vs_var_size_idx'),
        ),
        
        # Add indexes for Stock model
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['quantity_in_stock'], name='products_st_qty_in_idx'),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['-last_updated'], name='products_st_updated_idx'),
        ),
    ]
