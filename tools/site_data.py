"""Site data for davidecaputo.com. Plain data, no logic."""

ROLES = [
    dict(when="Nov 2026 – present", title="Senior Technical Architect", org="HM Revenue and Customs", detail=None),
    dict(when="Oct 2022 – Nov 2026", title="Senior Infrastructure Engineer", org="CreateFuture",
         detail="Led the Cyber Essentials Plus certification, owned identity and endpoint management, and built automation on AWS."),
    dict(when="Mar 2022 – Oct 2022", title="Infrastructure Engineer", org="BR-DGE",
         detail="Operated and secured the cloud platforms behind payment services."),
    dict(when="Apr 2019 – Mar 2022", title="IT Technician, then Infrastructure Engineer", org="Games Workshop",
         detail="Moved from IT support into infrastructure: device management, VPN and Google Workspace."),
    dict(when="2012 – 2019", title="Earlier roles", org="IT operations",
         detail="Networking, endpoint management and enterprise support."),
]

ACHIEVEMENTS = [
    ("Led the Cyber Essentials Plus certification", ", putting identity and endpoint controls in place to strengthen security."),
    ("Built automation", " with Python, APIs and AWS Lambda that cut manual operations and improved reliability."),
    ("Owned endpoint management", " for macOS and Windows with Jamf and Intune, improving compliance and device lifecycle."),
    ("Standardised joiner, mover and leaver processes", ", so access is consistent and security risk is lower."),
    ("Supported ISO and security audits", ", keeping systems ready for review."),
    ("Wrote documentation and runbooks", " that let teams work with less dependency on one person."),
]

SKILLS = [
    ("Identity and access", "Microsoft Entra ID (Azure AD), SSO integrations, RBAC, identity lifecycle"),
    ("Cloud platforms", "AWS, Microsoft Azure, Google Cloud Platform"),
    ("Automation", "Python, API integrations, Terraform concepts, AWS Lambda"),
    ("Endpoint management", "Jamf Pro (macOS), Microsoft Intune (Windows), device provisioning and compliance"),
    ("Security", "Cyber Essentials Plus, ISO certification support, VPN and access security"),
    ("Collaboration", "Google Workspace, Jira, Confluence, Bitbucket, GitHub, Slack, Microsoft Teams"),
]

CERTS = [
    ("OpenAI Practitioner Certifications", "2026"),
    ("AWS Certified Cloud Practitioner", "2024"),
    ("AWS Certified Developer, Associate", "in progress"),
    ("Atlassian Cloud Organisation Admin", "2024"),
    ("Jamf 100 Associate", "2023"),
    ("Cisco CCNA", "2012"),
]

EDU = [
    "Level 4 Network Infrastructure, Nottingham College",
    "Diploma in Information Technology, I.T.I.S. E. Barsanti",
]

ABOUT = [
    "I am a Senior Technical Architect at HM Revenue and Customs, where I started in November 2026. I have worked for over 10 years in identity, endpoint management, cloud and automation.",
    "I build secure, automated platforms. I write clear runbooks so teams can run systems on their own, and I write documentation that removes the dependency on one person.",
    "In my own time I build tools on GitHub. The public ones are listed on this site, from device management and AWS audits to Home Assistant integrations.",
]

PROJECTS = [
    dict(slug="jamf-snipe-it-suite", repo="Jamf-Snipe-IT-Suite", title="Jamf and Snipe-IT sync suite",
         blurb="Keeps Jamf Pro, Snipe-IT, Azure AD and HiBob in step on a schedule, handling joiners, leavers and rehires, with dry runs, on AWS Fargate.",
         lang="Python", group="work",
         tags=["jamf", "snipe-it", "azure-ad", "hibob", "aws", "fargate"]),
    dict(slug="aws-offboarding-audit", repo="AWS-Offboarding-Audit", title="AWS Offboarding Audit",
         blurb="Reads CloudTrail across every AWS account a leaver could reach, checks for backdoors and writes one local HTML report, with read-only access.",
         lang="Python", group="work",
         tags=["aws", "cloudtrail", "iam", "identity-center", "python", "offboarding"]),
    dict(slug="jamf-wakeup-call", repo="Jamf-WakeUp-Call", title="Jamf WakeUp Call",
         blurb="Redeploys the Jamf management framework on Macs that stopped checking in, by group, serial number or file, with a dry run; superseded by the wakeup module in Jamf-Snipe-IT-Suite.",
         lang="Python", group="work",
         tags=["jamf", "macos", "mdm", "python", "cli"]),
    dict(slug="ec2-linux-security-monitor", repo="EC2-Linux-Security-Monitor", title="EC2 Linux Security Monitor",
         blurb="Two Bash scripts and systemd timers that run ClamAV scans, quarantine and automatic security updates on Ubuntu and Amazon Linux, with an SSH status dashboard.",
         lang="Shell", group="work",
         tags=["aws", "ec2", "clamav", "bash", "systemd", "linux"]),
    dict(slug="new-starters-meetup", repo="New-Starters-Meetup", title="New Starters Meetup",
         blurb="A Slack command that books coffee and buddy intro meetings for new starters in Google Calendar, running on AWS Lambda.",
         lang="Python", group="work",
         tags=["slack", "aws", "lambda", "google-calendar", "python"]),
    dict(slug="payroll-mail-service", repo="Payroll-Mail-Service", title="Payroll Mail Service",
         blurb="A self-hosted mailer that matches payslip PDFs to staff, locks each one with an NI number and sends them in batches that stay under Gmail's daily limit.",
         lang="JavaScript", group="work",
         tags=["node", "express", "sqlite", "docker", "terraform", "gmail"]),
    dict(slug="itsd-reminder", repo="ITSD-Reminder", title="IT Service Desk Reminder",
         blurb="A Slack bot that reminds people once, in the ticket's thread, to pick a category on their IT Service Desk ticket.",
         lang="Python", group="work",
         tags=["slack", "python", "docker", "service-desk"]),
    dict(slug="mixergy-home-assistant", repo="Mixergy-Home-Assistant", title="Mixergy for Home Assistant",
         blurb="Shows how much hot water is left in a Mixergy tank and heats it when you choose, set up in the UI through HACS.",
         lang="Python", group="home",
         tags=["home-assistant", "hacs", "mixergy", "python", "energy"]),
    dict(slug="sunbridge-growatt-home-assistant", repo="SunBridge-Growatt-Home-Assistant", title="SunBridge for Growatt",
         blurb="Brings local Growatt solar data into Home Assistant straight from a ShineLan-X datalogger, with no cloud and no extra container.",
         lang="Python", group="home",
         tags=["home-assistant", "hacs", "growatt", "solar", "python"]),
    dict(slug="halfpast-meter-home-assistant", repo="HalfPast-Meter-Home-Assistant", title="HalfPast Meter",
         blurb="Imports a UK smart meter's half-hourly electricity and gas into the Home Assistant Energy dashboard through the Bright app.",
         lang="Python", group="home",
         tags=["home-assistant", "hacs", "smart-meter", "energy", "python"]),
    dict(slug="inkframe-immich", repo="InkFrame-Immich", title="InkFrame for Immich",
         blurb="Puts one well-chosen Immich photo on a battery e-paper frame every few days, with the source and the look controlled from Home Assistant.",
         lang="Python", group="home",
         tags=["immich", "esphome", "e-paper", "home-assistant", "docker"]),
    dict(slug="kallsup-sendspin-music-assistant", repo="Kallsup-Sendspin-Music-Assistant", title="Kallsup Sendspin speaker",
         blurb="Turns an IKEA KALLSUP into a battery-powered Wi-Fi speaker for Music Assistant, using an ESP32-S3 and ESPHome.",
         lang="Python", group="home",
         tags=["esphome", "esp32-s3", "music-assistant", "sendspin", "diy"]),
    dict(slug="macos-game-mode", repo="MacOS-Game-Mode", title="Game Mode for Mac",
         blurb="A free Mac app for cloud gamers that checks the Mac, Wi-Fi and internet, switches on Game Mode and shows which one causes the lag.",
         lang="Swift", group="home",
         tags=["macos", "swift", "swiftui", "game-mode", "cloud-gaming"]),
    dict(slug="keepsake-for-icloud", repo="Keepsake-for-iCloud", title="Keepsake for iCloud",
         blurb="Keeps your folders safe in iCloud Drive with a one-way mirror and a built-in web page.",
         lang="Python", group="home",
         tags=["icloud", "backup", "python", "docker", "macos"]),
]
