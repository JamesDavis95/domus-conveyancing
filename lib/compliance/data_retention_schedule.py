"""
Data Retention Schedule for Domus Conveyancing Platform
Comprehensive GDPR-compliant data retention policies
"""

DATA_RETENTION_SCHEDULE = """
# Data Retention Schedule

**Last Updated:** {last_updated}
**Version:** 2.0

## 1. Introduction

This Data Retention Schedule outlines how long we retain different types of personal data and the criteria for determining retention periods. This schedule supports our compliance with UK GDPR, Data Protection Act 2018, and professional regulations.

## 2. Legal and Regulatory Requirements

### 2.1 Solicitors Regulation Authority (SRA)
- **Conveyancing Files:** 15 years from completion
- **Client Account Records:** 15 years
- **Professional Correspondence:** 15 years
- **Compliance Records:** 15 years

### 2.2 HM Revenue & Customs (HMRC)
- **Financial Records:** 7 years from end of accounting period
- **VAT Records:** 6 years from end of VAT period
- **Employment Records:** 3 years after employment ends

### 2.3 Anti-Money Laundering (AML)
- **Identity Verification:** 5 years from end of business relationship
- **Due Diligence Records:** 5 years from completion of transaction
- **Suspicious Activity Reports:** 5 years from submission

### 2.4 Companies House
- **Statutory Records:** Permanently (for company records)
- **Board Minutes:** Permanently (for governance)

## 3. Data Categories and Retention Periods

### 3.1 Client Personal Data

**Identity and Contact Information:**
- **Retention Period:** 15 years from last transaction
- **Legal Basis:** SRA regulatory requirements
- **Review Trigger:** Annual compliance review
- **Disposal Method:** Secure deletion/shredding

**Financial Information:**
- **Bank Details:** 7 years from last use
- **Mortgage Information:** 15 years from transaction completion
- **Income Verification:** 7 years from transaction completion
- **Payment Records:** 7 years from payment date

**Property Information:**
- **Property Details:** 15 years from transaction completion
- **Search Results:** 15 years from transaction completion
- **Survey Reports:** 15 years from transaction completion
- **Title Documents:** 15 years from transaction completion

### 3.2 Legal and Professional Records

**Case Files:**
- **Active Matters:** Duration of matter plus 15 years
- **Completed Matters:** 15 years from completion
- **Aborted Matters:** 15 years from closure
- **Referred Matters:** 15 years from referral

**Legal Documents:**
- **Contracts and Agreements:** 15 years from execution
- **Correspondence:** 15 years from date of communication
- **Legal Opinions:** 15 years from provision
- **Court Documents:** 15 years from final order

**Professional Insurance:**
- **Claims Records:** 15 years from claim closure
- **Policy Documents:** 15 years from policy expiry
- **Incident Reports:** 15 years from incident date

### 3.3 Business and Administrative Data

**Employee Records:**
- **Personnel Files:** 7 years after employment ends
- **Payroll Records:** 7 years after tax year end
- **Training Records:** 7 years after completion
- **Disciplinary Records:** 7 years after resolution

**Financial Records:**
- **Accounting Records:** 7 years from year end
- **Invoices and Receipts:** 7 years from transaction
- **Bank Statements:** 7 years from statement date
- **Audit Records:** 7 years from audit completion

**Marketing and Communications:**
- **Marketing Lists:** Until consent withdrawn or 3 years inactive
- **Newsletter Subscriptions:** Until unsubscribed
- **Website Analytics:** 26 months from collection
- **Communication Logs:** 3 years from communication

### 3.4 Technical and Security Data

**Platform Usage Data:**
- **Access Logs:** 12 months from access
- **Security Logs:** 12 months from event
- **Performance Data:** 6 months from collection
- **Error Logs:** 6 months from occurrence

**Authentication Data:**
- **Login Records:** 12 months from login
- **2FA Setup Data:** Until 2FA disabled or account closed
- **Password History:** 12 months from change
- **Session Data:** 30 days from session end

**Backup Data:**
- **Daily Backups:** 30 days retention
- **Weekly Backups:** 12 weeks retention
- **Monthly Backups:** 12 months retention
- **Annual Backups:** 7 years retention

## 4. Retention Criteria

### 4.1 Primary Factors
- **Legal Requirements:** Statutory and regulatory obligations
- **Professional Standards:** SRA and professional body requirements
- **Business Necessity:** Operational and commercial needs
- **Risk Management:** Litigation and insurance considerations

### 4.2 Data Subject Rights
- **Erasure Requests:** Balanced against legal obligations
- **Legitimate Interests:** Ongoing legal and business needs
- **Consent Withdrawal:** Impact on retention periods
- **Data Portability:** Available during retention period

### 4.3 Data Minimization
- **Regular Reviews:** Annual assessment of retention necessity
- **Automated Deletion:** System-driven removal where possible
- **Data Archiving:** Move to secure archive storage
- **Pseudonymization:** Remove direct identifiers where possible

## 5. Retention Implementation

### 5.1 Automated Systems
**Database Retention:**
- Automated deletion scripts for expired data
- Regular cleanup of temporary and session data
- Archival processes for long-term storage
- Audit trails for all retention actions

**Document Management:**
- Automatic classification of document types
- Retention metadata for all stored documents
- Scheduled review and disposal processes
- Secure deletion verification

**Email and Communications:**
- Email retention policies in place
- Automatic archiving of old communications
- Secure disposal of deleted items
- Backup retention alignment

### 5.2 Manual Processes
**File Reviews:**
- Annual review of physical files
- Assessment of retention requirements
- Secure disposal of expired records
- Documentation of disposal actions

**Exception Handling:**
- Legal hold procedures for litigation
- Extended retention for regulatory inquiries
- Special handling for sensitive data
- Escalation processes for complex cases

## 6. Disposal Procedures

### 6.1 Electronic Data Disposal
**Secure Deletion:**
- Multi-pass overwriting of storage media
- Cryptographic key destruction for encrypted data
- Verification of complete data removal
- Certificate of destruction where required

**Cloud Data Disposal:**
- Coordination with cloud service providers
- Verification of data removal from all locations
- Backup and replica deletion
- Audit trail of disposal actions

### 6.2 Physical Document Disposal
**Confidential Shredding:**
- On-site or certified off-site shredding
- Cross-cut shredding for sensitive documents
- Certificate of destruction
- Supervised destruction where required

**Storage Media Disposal:**
- Physical destruction of storage devices
- Degaussing of magnetic media
- Certification of media destruction
- Audit trail of disposed items

## 7. Exceptions and Extensions

### 7.1 Legal Hold
When litigation or regulatory investigation is anticipated:
- Suspend normal retention schedules
- Preserve all relevant data and documents
- Document the legal hold process
- Release hold only when legally appropriate

### 7.2 Regulatory Inquiries
For SRA or other regulatory investigations:
- Extend retention of relevant records
- Cooperate with information requests
- Maintain audit trails of provided information
- Resume normal retention after inquiry closure

### 7.3 Insurance Claims
For professional indemnity or other claims:
- Retain all claim-related documentation
- Preserve communications and correspondence
- Maintain records until claim resolution
- Follow insurer requirements for retention

## 8. Data Subject Rights and Retention

### 8.1 Right to Erasure
**Balancing Test:**
- Legal obligations vs. erasure request
- Legitimate interests assessment
- Professional requirements consideration
- Risk evaluation for premature deletion

**Exceptions to Erasure:**
- Ongoing legal proceedings
- Regulatory compliance requirements
- Professional indemnity considerations
- Legitimate business interests

### 8.2 Data Portability
Available for:
- Personal data held during retention period
- Structured data in common formats
- Data processed with consent or for contract
- Data subject to automated processing

### 8.3 Rectification and Updates
- Ongoing obligation during retention period
- Update procedures for corrected information
- Notification to third parties where appropriate
- Audit trail of all corrections

## 9. Monitoring and Review

### 9.1 Regular Reviews
**Annual Assessment:**
- Review of retention periods and criteria
- Assessment of legal and regulatory changes
- Evaluation of disposal procedures
- Update of retention schedules

**Compliance Monitoring:**
- Regular audits of retention practices
- Assessment of disposal procedures
- Review of automation effectiveness
- Training and awareness programs

### 9.2 Documentation
**Retention Records:**
- Log of all retention decisions
- Documentation of disposal actions
- Audit trails for data lifecycle
- Exception and extension records

**Policy Updates:**
- Version control for retention schedules
- Change logs and approval records
- Communication of policy updates
- Training materials and guidance

## 10. Responsibilities

### 10.1 Data Protection Officer
- Overall retention policy oversight
- Compliance monitoring and reporting
- Data subject rights coordination
- Regulatory liaison and reporting

### 10.2 IT Department
- Technical implementation of retention
- Automated deletion systems
- Secure disposal procedures
- Backup and archival management

### 10.3 Legal Department
- Legal hold procedures
- Regulatory compliance guidance
- Litigation support
- Professional requirement interpretation

### 10.4 All Staff
- Compliance with retention policies
- Identification of retention issues
- Proper data handling and disposal
- Incident reporting and escalation

## 11. Contact Information

**Data Protection Officer:**
Email: dpo@domusconveyancing.co.uk
Phone: 020 1234 5678

**Records Management:**
Email: records@domusconveyancing.co.uk

**IT Support:**
Email: itsupport@domusconveyancing.co.uk

---

This Data Retention Schedule is reviewed annually and updated as necessary to reflect changes in law, regulation, and business requirements. All staff are required to comply with these retention periods and procedures.
"""

def get_data_retention_schedule(last_updated=None):
    """Get formatted data retention schedule"""
    
    if not last_updated:
        from datetime import datetime
        last_updated = datetime.now().strftime("%d %B %Y")
    
    return DATA_RETENTION_SCHEDULE.format(last_updated=last_updated)