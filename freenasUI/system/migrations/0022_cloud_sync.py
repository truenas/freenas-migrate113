# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-05-13 10:49
from __future__ import unicode_literals

import base64
from Cryptodome.Cipher import AES
from django.db import migrations, models
import json


PWENC_BLOCK_SIZE = 32
PWENC_FILE_SECRET = '/data/pwenc_secret'
PWENC_PADDING = b'{'
PWENC_CHECK = 'Donuts!'


def pwenc_get_secret():
    with open(PWENC_FILE_SECRET, 'rb') as f:
        secret = f.read()
    return secret


def pwenc_encrypt(text):
    if not isinstance(text, bytes):
        text = text.encode('utf8')
    from Cryptodome.Random import get_random_bytes
    from Cryptodome.Util import Counter

    def pad(x):
        return x + (PWENC_BLOCK_SIZE - len(x) % PWENC_BLOCK_SIZE) * PWENC_PADDING

    nonce = get_random_bytes(8)
    cipher = AES.new(
        pwenc_get_secret(),
        AES.MODE_CTR,
        counter=Counter.new(64, prefix=nonce),
    )
    encoded = base64.b64encode(nonce + cipher.encrypt(pad(text)))
    return encoded.decode()


def pwenc_decrypt(encrypted=None):
    if not encrypted:
        return ""
    from Cryptodome.Util import Counter
    encrypted = base64.b64decode(encrypted)
    nonce = encrypted[:8]
    encrypted = encrypted[8:]
    cipher = AES.new(
        pwenc_get_secret(),
        AES.MODE_CTR,
        counter=Counter.new(64, prefix=nonce),
    )
    return cipher.decrypt(encrypted).rstrip(PWENC_PADDING).decode('utf8')


def migrate_cloud_credentials(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        for id, provider, attributes in cursor.execute("SELECT id, provider, attributes FROM system_cloudcredentials").fetchall():
            try:
                attributes = json.loads(pwenc_decrypt(attributes))
            except (UnicodeDecodeError, json.decoder.JSONDecodeError):
                # Running migration with an invalid pwenc_secret
                continue

            if provider == "AMAZON":
                provider = "S3"
                attributes = {
                    "access_key_id": attributes["access_key"],
                    "secret_access_key": attributes["secret_key"],
                    "endpoint": attributes.get("endpoint", ""),
                }

            if provider == "AZURE":
                provider = "AZUREBLOB"
                attributes = {
                    "account": attributes["account_name"],
                    "key": attributes["account_key"],
                }

            if provider == "BACKBLAZE":
                provider = "B2"
                attributes = {
                    "account": attributes["account_id"],
                    "key": attributes["app_key"],
                }

            if provider == "GCLOUD":
                provider = "GOOGLE_CLOUD_STORAGE"
                attributes = {
                    "service_account_credentials": json.dumps(attributes["keyfile"]),
                }

            cursor.execute("UPDATE system_cloudcredentials SET provider = %s, attributes = %s WHERE id = %s", [
                provider, pwenc_encrypt(json.dumps(attributes)), id])


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0022_cert_serial'),
    ]

    operations = [
        migrations.RunPython(migrate_cloud_credentials),
    ]
