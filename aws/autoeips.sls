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
    - name: |
        python /usr/local/bin/autoeips.py
         --eips '{{aws.eips | json()}}'
         --log-level {{ aws.log_level }}
         --log-format {{ aws.log_format }}
         --log-file {{ aws.log_file }}
         {% if aws.eip_enable_standby_mode %}--enable-standby-mode{% endif %}
         {% if aws.eip_enable_failover_mode %}--enable-failover-mode{% endif %}
    - user: root
    - minute: "*/1"
