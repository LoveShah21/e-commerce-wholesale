# Generated migration for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0003_rawmaterial_last_updated'),
    ]

    operations = [
        # Add indexes for RawMaterial model
        migrations.AddIndex(
            model_name='rawmaterial',
            index=models.Index(fields=['material_type'], name='mfg_rm_type_idx'),
        ),
        migrations.AddIndex(
            model_name='rawmaterial',
            index=models.Index(fields=['current_quantity'], name='mfg_rm_qty_idx'),
        ),
        migrations.AddIndex(
            model_name='rawmaterial',
            index=models.Index(fields=['-last_updated'], name='mfg_rm_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='rawmaterial',
            index=models.Index(fields=['material_name'], name='mfg_rm_name_idx'),
        ),
        
        # Add indexes for MaterialSupplier model
        migrations.AddIndex(
            model_name='materialsupplier',
            index=models.Index(fields=['material', 'supplier'], name='mfg_ms_mat_sup_idx'),
        ),
        migrations.AddIndex(
            model_name='materialsupplier',
            index=models.Index(fields=['is_preferred'], name='mfg_ms_preferred_idx'),
        ),
        migrations.AddIndex(
            model_name='materialsupplier',
            index=models.Index(fields=['material', 'is_preferred'], name='mfg_ms_mat_pref_idx'),
        ),
        
        # Add indexes for ManufacturingSpecification model
        migrations.AddIndex(
            model_name='manufacturingspecification',
            index=models.Index(fields=['variant_size'], name='mfg_spec_vs_idx'),
        ),
        migrations.AddIndex(
            model_name='manufacturingspecification',
            index=models.Index(fields=['material'], name='mfg_spec_mat_idx'),
        ),
        migrations.AddIndex(
            model_name='manufacturingspecification',
            index=models.Index(fields=['variant_size', 'material'], name='mfg_spec_vs_mat_idx'),
        ),
        
        # Add indexes for Supplier model
        migrations.AddIndex(
            model_name='supplier',
            index=models.Index(fields=['supplier_name'], name='mfg_sup_name_idx'),
        ),
    ]
