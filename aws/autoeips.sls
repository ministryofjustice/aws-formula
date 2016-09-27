{% from "aws/map.jinja" import aws with context %}
autoeips_cron:
  pkg.installed:
    - name: cron
  service.running:
    - name: cron

autoeips.py:
  file.managed:
    - name: /usr/local/bin/autoeips.py
    - source: salt://aws/files/autoeips.py
    - user: root
    - group: root
    - mode: 755
    - template: jinja

boto3:
  pip.installed:
    - user: root

cron_cleanup:
  cmd.run:
    - name: crontab -l | grep -v 'autoeips.py'  | crontab -
    - require_in:
      - state: cron_autoeips

cron_autoeips:
  cron.present:
    - name: python /usr/local/bin/autoeips.py >> {{ aws.auto_eip_log }} 2>&1
    - user: root
    - minute: "*/1"
