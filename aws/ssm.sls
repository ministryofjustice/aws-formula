{% from "aws/map.jinja" import aws with context %}

amazon-ssm-agent-download:
  cmd.run:
    - name: curl -L https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/debian_amd64/amazon-ssm-agent.deb -o /tmp/amazon-ssm-agent.deb
    - creates: /tmp/amazon-ssm-agent.deb

amazon-ssm-agent-install:
  cmd.run:
    - name: sudo dpkg -i /tmp/amazon-ssm-agent.deb
    - onchanges:
      - cmd: amazon-ssm-agent-download

amazon-ssm-agent.json:
  file.managed:
    - name: /etc/amazon/ssm/amazon-ssm-agent.json
    - source: salt://aws/files/amazon-ssm-agent.json
    - template: jinja
    - onchanges:
      - cmd: amazon-ssm-agent-install

amazon-ssm-agent:
  service.running:
    - enable: True
    - reload: True
    - watch:
      - file: amazon-ssm-agent.json
    - onchanges:
      - cmd: amazon-ssm-agent-install
