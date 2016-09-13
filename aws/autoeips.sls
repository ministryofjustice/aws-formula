autoeips.py:
  file.managed:
    - name: /usr/local/bin/autoeips.py
    - source: salt://aws/files/autoeips.py
    - user: root
    - group: root
    - mode: 755
    - template: jinja

cron_autoeips:
  cron.present:
    - name: python /usr/local/bin/autoeips.py >> /var/log/autoeips.log
    - user: root
    - minute: "*/1"