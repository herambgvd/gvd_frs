"""Tenants and License Fix

Revision ID: 1a9d9e4d7242
Revises: b6cb7200645d
Create Date: 2025-09-29 07:45:18.352657+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1a9d9e4d7242'
down_revision: Union[str, Sequence[str], None] = 'b6cb7200645d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ENUM type first
    tenantstatus_enum = postgresql.ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING', name='tenantstatus')
    tenantstatus_enum.create(op.get_bind())

    # Drop foreign key constraint first (if it exists)
    try:
        op.drop_constraint('fk_licenses_tenant_id_tenants', 'licenses', type_='foreignkey')
    except Exception:
        # Constraint might not exist, continue
        pass

    # Modify licenses table
    op.add_column('licenses', sa.Column('client_name', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('licenses', sa.Column('client_id', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('licenses', sa.Column('permissions', sa.Text(), nullable=True))
    op.add_column('licenses', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('licenses', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('licenses', sa.Column('usage_limit', sa.Integer(), nullable=True))
    op.add_column('licenses', sa.Column('current_usage', sa.Integer(), nullable=False, server_default='0'))

    # Change tenant_id type in licenses table
    op.alter_column('licenses', 'tenant_id',
                   existing_type=sa.INTEGER(),
                   type_=sa.String(length=255),
                   nullable=True)

    # Drop and recreate indexes
    try:
        op.drop_index('ix_licenses_tenant_id', table_name='licenses')
    except Exception:
        pass
    op.create_index(op.f('ix_licenses_client_id'), 'licenses', ['client_id'], unique=True)

    # Drop old columns
    columns_to_drop = ['status', 'license_type', 'metadata_json', 'description', 'valid_from', 'valid_until']
    for column in columns_to_drop:
        try:
            op.drop_column('licenses', column)
        except Exception:
            # Column might not exist, continue
            pass

    # Modify tenants table
    op.add_column('tenants', sa.Column('domain', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('status', tenantstatus_enum, nullable=False, server_default='ACTIVE'))
    op.add_column('tenants', sa.Column('max_users', sa.Integer(), nullable=True))
    op.add_column('tenants', sa.Column('current_users', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tenants', sa.Column('created_by', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('contact_email', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('contact_phone', sa.String(length=50), nullable=True))

    # Change id type in tenants table
    op.alter_column('tenants', 'id',
                   existing_type=sa.INTEGER(),
                   type_=sa.String(length=255),
                   existing_nullable=False)

    # Drop old indexes
    old_indexes = ['ix_tenants_email', 'ix_tenants_name', 'ix_tenants_slug']
    for index_name in old_indexes:
        try:
            op.drop_index(index_name, table_name='tenants')
        except Exception:
            pass

    op.create_index(op.f('ix_tenants_domain'), 'tenants', ['domain'], unique=True)

    # Drop old columns from tenants
    tenant_columns_to_drop = ['is_active', 'contact_person', 'address', 'phone', 'email', 'slug']
    for column in tenant_columns_to_drop:
        try:
            op.drop_column('tenants', column)
        except Exception:
            # Column might not exist, continue
            pass

    # Recreate foreign key constraint with new types
    op.create_foreign_key('fk_licenses_tenant_id_tenants', 'licenses', 'tenants', ['tenant_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint first
    try:
        op.drop_constraint('fk_licenses_tenant_id_tenants', 'licenses', type_='foreignkey')
    except Exception:
        pass

    # Restore tenants table
    op.add_column('tenants', sa.Column('slug', sa.VARCHAR(length=100), autoincrement=False, nullable=False, server_default=''))
    op.add_column('tenants', sa.Column('email', sa.VARCHAR(length=255), autoincrement=False, nullable=False, server_default=''))
    op.add_column('tenants', sa.Column('phone', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('tenants', sa.Column('address', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('tenants', sa.Column('contact_person', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('tenants', sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False, server_default='true'))

    try:
        op.drop_index(op.f('ix_tenants_domain'), table_name='tenants')
    except Exception:
        pass
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)
    op.create_index('ix_tenants_name', 'tenants', ['name'], unique=False)
    op.create_index('ix_tenants_email', 'tenants', ['email'], unique=True)

    # Change tenants.id type back to INTEGER
    op.alter_column('tenants', 'id',
                   existing_type=sa.String(length=255),
                   type_=sa.INTEGER(),
                   existing_nullable=False)

    # Drop new columns from tenants
    new_tenant_columns = ['contact_phone', 'contact_email', 'created_by', 'current_users', 'max_users', 'status', 'domain']
    for column in new_tenant_columns:
        try:
            op.drop_column('tenants', column)
        except Exception:
            pass

    # Restore licenses table
    op.add_column('licenses', sa.Column('valid_until', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('licenses', sa.Column('valid_from', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False, server_default=sa.func.now()))
    op.add_column('licenses', sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('licenses', sa.Column('metadata_json', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('licenses', sa.Column('license_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False, server_default='standard'))
    op.add_column('licenses', sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=False, server_default='active'))

    try:
        op.drop_index(op.f('ix_licenses_client_id'), table_name='licenses')
    except Exception:
        pass
    op.create_index('ix_licenses_tenant_id', 'licenses', ['tenant_id'], unique=False)

    # Change licenses.tenant_id type back to INTEGER
    op.alter_column('licenses', 'tenant_id',
                   existing_type=sa.String(length=255),
                   type_=sa.INTEGER(),
                   nullable=True)

    # Drop new columns from licenses
    new_license_columns = ['current_usage', 'usage_limit', 'expires_at', 'is_active', 'permissions', 'client_id', 'client_name']
    for column in new_license_columns:
        try:
            op.drop_column('licenses', column)
        except Exception:
            pass

    # Recreate foreign key constraint with original types
    op.create_foreign_key('fk_licenses_tenant_id_tenants', 'licenses', 'tenants', ['tenant_id'], ['id'])

    # Drop ENUM type
    tenantstatus_enum = postgresql.ENUM(name='tenantstatus')
    tenantstatus_enum.drop(op.get_bind())
