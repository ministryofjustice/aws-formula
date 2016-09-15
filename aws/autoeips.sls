{% from "aws/map.jinja" import aws with context %}
autoeips.py:
  file.managed:
    - name: /usr/local/bin/autoeips.py
    - source: salt://aws/files/autoeips.py
    - user: root
    - group: root
    - mode: 755
    - template: jinja

boto3:
  pkg.installed

cron_autoeips:
  cron.present:
    - name: python /usr/local/bin/autoeips.py >> {{ aws.auto_eip_log }}
    - user: root
    - minute: "*/1"
