# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-04-29 06:31
from __future__ import unicode_literals

import base64
from Cryptodome.Cipher import AES
from django.conf import settings
from django.db import migrations, models


PWENC_BLOCK_SIZE = 32
PWENC_PADDING = b'{'
PWENC_CHECK = 'Donuts!'


def pwenc_get_secret():
    with open(settings.PWENC_FILE_SECRET, 'rb') as f:
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


def encrypt_db(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        for table, fields in [
            ("services_snmp", ["snmp_v3_password", "snmp_v3_privpassphrase"]),
            ("services_ssh", ["ssh_privatekey", "ssh_host_dsa_key", "ssh_host_ecdsa_key", "ssh_host_ed25519_key",
                              "ssh_host_key", "ssh_host_rsa_key"]),
            ("services_s3", ["s3_secret_key"]),
            ("system_certificate", ["cert_privatekey"]),
            ("system_certificateauthority", ["cert_privatekey"]),
        ]:
            cursor.execute(f"SELECT * FROM {table}")
            columns = [col[0] for col in cursor.description]
            rows = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
            for row in rows:
                set = []
                params = []
                for k in fields:
                    if row[k] is not None:
                        set.append(f"{k} = %s")
                        params.append(pwenc_encrypt(row[k]))

                if set:
                    cursor.execute(f"UPDATE {table} SET {', '.join(set)} WHERE id = {row['id']}", params)

        cursor.execute("INSERT INTO system_keyvalue (key, value) VALUES ('has_0039_auto_20200429_0631', 'true')")


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0038_disable_capabilities'),
    ]

    operations = [
        migrations.RunPython(
            encrypt_db,
        ),
    ]
