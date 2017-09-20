{% from "aws/map.jinja" import aws with context %}

awslogs-agent-setup:
  cmd.run:
    - name: curl -L https://s3.amazonaws.com/aws-cloudwatch/downloads/latest/awslogs-agent-setup.py -o /tmp/awslogs-agent-setup.py
    - creates: /tmp/awslogs-agent-setup.py

awslogs-agent-setup-run:
  cmd.run:
    - name: python /tmp/awslogs-agent-setup.py -n -r eu-west-1 -c /tmp/awslogs.conf
    - onchanges:
      - file: awslogs.conf
    - require:
      - cmd: awslogs-agent-setup
      - file: awslogs.conf


awslogs.conf:
  file.managed:
    - name: /tmp/awslogs.conf
    - source: salt://aws/files/awslogs.conf
    - template: jinja

awslogs:
  service.running:
    - enable: True
    - onchanges:
      - cmd: awslogs-agent-setup-run
