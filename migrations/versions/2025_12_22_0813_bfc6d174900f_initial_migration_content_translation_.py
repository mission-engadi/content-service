"""Initial migration: Content, Translation, and Media models

Revision ID: bfc6d174900f
Revises: 
Create Date: 2025-12-22 08:13:08.492351+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bfc6d174900f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create enums
    content_type_enum = postgresql.ENUM(
        'story', 'update', 'testimonial', 'prayer_request', 'blog_post',
        name='content_type_enum',
        create_type=False
    )
    content_type_enum.create(op.get_bind(), checkfirst=True)
    
    content_status_enum = postgresql.ENUM(
        'draft', 'review', 'published', 'archived',
        name='content_status_enum',
        create_type=False
    )
    content_status_enum.create(op.get_bind(), checkfirst=True)
    
    translation_status_enum = postgresql.ENUM(
        'pending', 'in_progress', 'completed', 'reviewed',
        name='translation_status_enum',
        create_type=False
    )
    translation_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create content table
    op.create_table(
        'content',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('slug', sa.String(length=500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('content_type', content_type_enum, nullable=False),
        sa.Column('status', content_status_enum, nullable=False, server_default='draft'),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('featured_image_url', sa.String(length=1000), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for content table
    op.create_index('ix_content_id', 'content', ['id'])
    op.create_index('ix_content_slug', 'content', ['slug'], unique=True)
    op.create_index('ix_content_title', 'content', ['title'])
    op.create_index('ix_content_content_type', 'content', ['content_type'])
    op.create_index('ix_content_status', 'content', ['status'])
    op.create_index('ix_content_author_id', 'content', ['author_id'])
    op.create_index('ix_content_language', 'content', ['language'])
    op.create_index('ix_content_published_at', 'content', ['published_at'])
    op.create_index('idx_content_type_status', 'content', ['content_type', 'status'])
    op.create_index('idx_language_status', 'content', ['language', 'status'])
    op.create_index('idx_author_status', 'content', ['author_id', 'status'])
    op.create_index('idx_published_at_desc', 'content', [sa.text('published_at DESC')])
    
    # Create translations table
    op.create_table(
        'translations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('translated_title', sa.String(length=500), nullable=False),
        sa.Column('translated_body', sa.Text(), nullable=False),
        sa.Column('translated_slug', sa.String(length=500), nullable=False),
        sa.Column('translator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('translation_status', translation_status_enum, nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for translations table
    op.create_index('ix_translations_id', 'translations', ['id'])
    op.create_index('ix_translations_content_id', 'translations', ['content_id'])
    op.create_index('ix_translations_language', 'translations', ['language'])
    op.create_index('ix_translations_translated_title', 'translations', ['translated_title'])
    op.create_index('ix_translations_translated_slug', 'translations', ['translated_slug'])
    op.create_index('ix_translations_translator_id', 'translations', ['translator_id'])
    op.create_index('ix_translations_translation_status', 'translations', ['translation_status'])
    op.create_index('idx_content_language', 'translations', ['content_id', 'language'], unique=True)
    op.create_index('idx_translation_status', 'translations', ['translation_status'])
    op.create_index('idx_language_status_trans', 'translations', ['language', 'translation_status'])
    
    # Create media table
    op.create_table(
        'media',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('media_type', sa.String(length=20), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('storage_path', sa.String(length=1000), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for media table
    op.create_index('ix_media_id', 'media', ['id'])
    op.create_index('ix_media_content_id', 'media', ['content_id'])
    op.create_index('ix_media_media_type', 'media', ['media_type'])
    op.create_index('ix_media_url', 'media', ['url'])
    op.create_index('ix_media_uploaded_by', 'media', ['uploaded_by'])
    op.create_index('idx_media_type_content', 'media', ['media_type', 'content_id'])
    op.create_index('idx_uploaded_by_created', 'media', ['uploaded_by', 'created_at'])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop tables
    op.drop_table('media')
    op.drop_table('translations')
    op.drop_table('content')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS translation_status_enum')
    op.execute('DROP TYPE IF EXISTS content_status_enum')
    op.execute('DROP TYPE IF EXISTS content_type_enum')
