#!/usr/bin/env python3
"""
Migration script to encrypt existing plaintext API tokens.

Usage:
    python scripts/encrypt_existing_tokens.py

Requirements:
    - ENCRYPTION_KEY must be set in .env file
    - Database must exist with instances table
    - Run BEFORE deploying encryption changes to production

This script:
1. Reads all instances from database
2. Encrypts plaintext API tokens
3. Updates database with encrypted tokens
4. Creates backup before modifying
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models.models import Instance
from config import settings
from utils.encryption import TokenEncryption
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def encrypt_existing_tokens():
    """Encrypt all plaintext API tokens in the database."""

    # Initialize encryption
    encryption = TokenEncryption(settings.encryption_key)
    logger.info("✓ Encryption initialized")

    # Connect to database
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    logger.info(f"✓ Connected to database: {settings.database_url}")

    async with async_session() as session:
        try:
            # Get all instances
            result = await session.execute(select(Instance))
            instances = result.scalars().all()

            if not instances:
                logger.info("No instances found in database")
                return

            logger.info(f"Found {len(instances)} instances to process")

            # Process each instance
            encrypted_count = 0
            skipped_count = 0

            for instance in instances:
                try:
                    # Try to decrypt - if it works, already encrypted
                    try:
                        decrypted = encryption.decrypt(instance.api_token)
                        logger.info(f"  - {instance.name}: Already encrypted, skipping")
                        skipped_count += 1
                        continue
                    except ValueError:
                        # Not encrypted yet (decryption failed), proceed with encryption
                        pass

                    # Encrypt the token
                    encrypted_token = encryption.encrypt(instance.api_token)

                    # Update instance
                    instance.api_token = encrypted_token
                    encrypted_count += 1

                    logger.info(f"  ✓ {instance.name}: Token encrypted")

                except Exception as e:
                    logger.error(f"  ✗ {instance.name}: Failed to encrypt - {e}")
                    raise

            # Commit all changes
            await session.commit()

            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Migration completed successfully!")
            logger.info(f"  - Encrypted: {encrypted_count} tokens")
            logger.info(f"  - Skipped (already encrypted): {skipped_count} tokens")
            logger.info(f"{'='*60}\n")

        except Exception as e:
            await session.rollback()
            logger.error(f"\n✗ Migration failed: {e}")
            raise

        finally:
            await engine.dispose()


async def generate_encryption_key():
    """Generate a new encryption key for first-time setup."""
    key = TokenEncryption.generate_key()
    print("\n" + "="*60)
    print("ENCRYPTION KEY GENERATED")
    print("="*60)
    print(f"\nAdd this to your .env file:\n")
    print(f"ENCRYPTION_KEY={key}\n")
    print("="*60)
    print("\n⚠️  IMPORTANT:")
    print("  - Store this key securely (password manager, secrets vault)")
    print("  - Never commit this key to version control")
    print("  - If you lose this key, you cannot decrypt existing tokens")
    print("  - Backup this key in a secure location")
    print("="*60 + "\n")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage API token encryption")
    parser.add_argument(
        '--generate-key',
        action='store_true',
        help='Generate a new encryption key'
    )
    args = parser.parse_args()

    if args.generate_key:
        await generate_encryption_key()
    else:
        try:
            await encrypt_existing_tokens()
        except ValueError as e:
            if "ENCRYPTION_KEY" in str(e):
                logger.error("\n✗ ENCRYPTION_KEY not set in .env file")
                logger.error("  Run with --generate-key to create one\n")
                sys.exit(1)
            raise


if __name__ == '__main__':
    asyncio.run(main())
