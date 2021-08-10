# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-03-21 16:27
from __future__ import unicode_literals

import base64
from Cryptodome.Cipher import AES
from django.db import migrations, models
import freenasUI.freeadmin.models.fields


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


def encrypt_cloud_credentials(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        for id, attributes in cursor.execute("SELECT id, attributes FROM system_cloudcredentials").fetchall():
            cursor.execute("UPDATE system_cloudcredentials SET attributes = %s WHERE id = %s", [
                pwenc_encrypt(attributes), id])


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0009_auto_20171023_2159'),
    ]

    operations = [
        migrations.RunPython(encrypt_cloud_credentials),
    ]
