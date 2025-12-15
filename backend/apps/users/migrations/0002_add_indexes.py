# Generated migration for adding database indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        # Add indexes for User model
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_user_email_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['user_type', 'account_status'], name='users_user_type_status_idx'),
        ),
        
        # Add indexes for Address model
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['user', 'is_default'], name='users_addr_user_default_idx'),
        ),
        
        # Add indexes for State model
        migrations.AddIndex(
            model_name='state',
            index=models.Index(fields=['country'], name='users_state_country_idx'),
        ),
        
        # Add indexes for City model
        migrations.AddIndex(
            model_name='city',
            index=models.Index(fields=['state'], name='users_city_state_idx'),
        ),
        
        # Add indexes for PostalCode model
        migrations.AddIndex(
            model_name='postalcode',
            index=models.Index(fields=['city'], name='users_postal_city_idx'),
        ),
        migrations.AddIndex(
            model_name='postalcode',
            index=models.Index(fields=['postal_code'], name='users_postal_code_idx'),
        ),
    ]
