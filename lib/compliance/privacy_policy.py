"""
Privacy Policy for Domus Conveyancing Platform
Comprehensive GDPR-compliant privacy policy
"""

PRIVACY_POLICY = """
# Privacy Policy

**Last Updated:** {last_updated}
**Effective Date:** {effective_date}

## 1. Introduction

Domus Conveyancing Limited ("we," "our," or "us") is committed to protecting your privacy and personal data. This Privacy Policy explains how we collect, use, store, and protect your information when you use our conveyancing platform and services.

We are the data controller for the personal data we process about you. Our registered office is located in the United Kingdom, and we comply with the UK General Data Protection Regulation (UK GDPR) and the Data Protection Act 2018.

## 2. Information We Collect

### 2.1 Personal Information
We collect the following types of personal information:

**Identity Data:**
- Full name, title, date of birth
- National Insurance number
- Passport or driving licence details
- Photographs for identity verification

**Contact Data:**
- Email addresses
- Telephone numbers
- Postal addresses (current and previous)

**Financial Data:**
- Bank account details
- Mortgage information
- Income verification documents
- Credit history (where applicable)

**Property Data:**
- Property addresses and details
- Purchase/sale information
- Survey and valuation reports
- Land registry information

**Legal Data:**
- Legal documents and contracts
- Correspondence with solicitors
- Court documents (if applicable)
- Compliance and regulatory records

### 2.2 Technical Data
We automatically collect:
- IP addresses and device identifiers
- Browser type and version
- Operating system and platform
- Website usage data and analytics
- Cookies and tracking technologies

### 2.3 Communication Data
- Messages sent through our platform
- Email correspondence
- Phone call recordings (with consent)
- Customer support interactions

## 3. How We Use Your Information

### 3.1 Legal Basis for Processing
We process your personal data under the following legal bases:

**Contract Performance:**
- Providing conveyancing services
- Managing property transactions
- Processing payments and fees

**Legal Obligation:**
- Anti-money laundering checks
- Right to work verification
- Regulatory compliance reporting
- Court orders and legal requirements

**Legitimate Interest:**
- Fraud prevention and security
- Service improvement and analytics
- Marketing communications (with opt-out)
- Business administration

**Consent:**
- Marketing communications
- Optional service features
- Third-party integrations

### 3.2 Purposes of Processing
We use your information to:

**Service Delivery:**
- Complete property transactions
- Conduct legal searches and checks
- Prepare and review legal documents
- Coordinate with estate agents, lenders, and other parties

**Compliance and Security:**
- Verify your identity and prevent fraud
- Comply with anti-money laundering regulations
- Meet professional and regulatory obligations
- Maintain audit trails and records

**Communication:**
- Send transaction updates and notifications
- Provide customer support
- Send service-related communications
- Share relevant legal and regulatory updates

**Business Operations:**
- Improve our services and platform
- Conduct data analytics and reporting
- Train our staff and systems
- Manage our business relationships

## 4. Information Sharing and Disclosure

### 4.1 Third Parties We Share With
We may share your information with:

**Essential Service Providers:**
- HM Land Registry
- Local authority search providers
- Environmental search companies
- Bank and lender institutions
- Survey and valuation companies

**Professional Partners:**
- Estate agents and property professionals
- Other solicitors and legal professionals
- Accountants and financial advisors
- Insurance companies

**Regulatory and Legal:**
- HM Revenue & Customs
- Solicitors Regulation Authority
- Court services and tribunals
- Law enforcement agencies
- Anti-money laundering authorities

**Technology Partners:**
- Cloud hosting providers (AWS, Google Cloud)
- Payment processors (Stripe)
- Identity verification services
- Document management systems
- Communication platforms

### 4.2 International Transfers
Some of our service providers are located outside the UK/EEA. We ensure adequate protection through:
- Adequacy decisions by the UK Government
- Standard Contractual Clauses (SCCs)
- Binding Corporate Rules
- Certification schemes

### 4.3 Data Sharing Principles
We only share information when:
- Necessary for service delivery
- Required by law or regulation
- With your explicit consent
- Protected by appropriate safeguards

## 5. Data Retention

### 5.1 Retention Periods
We retain your data for the following periods:

**Active Transactions:**
- Throughout the transaction period
- Plus 6 months for completion activities

**Completed Transactions:**
- 15 years for conveyancing files (SRA requirement)
- 7 years for financial records (tax requirements)
- 6 years for general business records

**Marketing Data:**
- Until you withdraw consent
- Maximum 3 years without engagement

**Technical Data:**
- 12 months for analytics data
- 30 days for log files

### 5.2 Secure Disposal
When retention periods expire, we:
- Securely delete electronic records
- Shred physical documents
- Maintain disposal logs
- Verify complete removal

## 6. Your Rights Under GDPR

### 6.1 Individual Rights
You have the right to:

**Access:** Request copies of your personal data
**Rectification:** Correct inaccurate or incomplete data
**Erasure:** Request deletion of your data (subject to legal obligations)
**Restriction:** Limit how we process your data
**Portability:** Receive your data in a structured format
**Objection:** Object to processing based on legitimate interests
**Automated Decision-Making:** Not be subject to solely automated decisions

### 6.2 How to Exercise Rights
To exercise your rights:
- Email: privacy@domusconveyancing.co.uk
- Phone: 020 1234 5678
- Post: Data Protection Officer, Domus Conveyancing Limited, [Address]

We will respond within one month of receiving your request.

### 6.3 Right to Complain
You can lodge a complaint with:
- Information Commissioner's Office (ICO)
- Phone: 0303 123 1113
- Website: ico.org.uk

## 7. Data Security

### 7.1 Technical Measures
We protect your data with:
- End-to-end encryption in transit and at rest
- Multi-factor authentication
- Regular security monitoring and testing
- Secure cloud infrastructure
- Regular backup and recovery procedures

### 7.2 Organizational Measures
- Staff training on data protection
- Access controls and audit trails
- Data protection impact assessments
- Incident response procedures
- Regular policy reviews and updates

### 7.3 Breach Notification
In case of a data breach, we will:
- Notify the ICO within 72 hours
- Inform affected individuals if high risk
- Investigate and remediate the issue
- Review and improve security measures

## 8. Cookies and Tracking

### 8.1 Types of Cookies
We use:

**Essential Cookies:** Required for platform functionality
**Analytics Cookies:** To understand usage patterns
**Preference Cookies:** To remember your settings
**Marketing Cookies:** For targeted communications (with consent)

### 8.2 Managing Cookies
You can control cookies through:
- Your browser settings
- Our cookie preference center
- Opt-out links in communications

## 9. Children's Privacy

Our services are not intended for individuals under 18. We do not knowingly collect personal data from children. If you believe we have collected such data, please contact us immediately.

## 10. Changes to This Policy

We may update this Privacy Policy to reflect:
- Changes in law or regulation
- New features or services
- Feedback from regulators or users

We will notify you of significant changes through:
- Email notifications
- Platform announcements
- Website notices

## 11. Contact Information

**Data Protection Officer:**
Email: dpo@domusconveyancing.co.uk
Phone: 020 1234 5678

**General Enquiries:**
Email: privacy@domusconveyancing.co.uk
Website: www.domusconveyancing.co.uk

**Postal Address:**
Domus Conveyancing Limited
Data Protection Team
[Full Address]
United Kingdom

---

This Privacy Policy is part of our commitment to transparency and data protection. We regularly review and update our practices to ensure the highest standards of privacy protection for our clients.
"""

def get_privacy_policy(last_updated=None, effective_date=None):
    """Get formatted privacy policy"""
    
    if not last_updated:
        from datetime import datetime
        last_updated = datetime.now().strftime("%d %B %Y")
    
    if not effective_date:
        effective_date = "1 January 2024"
    
    return PRIVACY_POLICY.format(
        last_updated=last_updated,
        effective_date=effective_date
    )