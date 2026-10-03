"""
Utility script to generate a sample court order document for testing OrderGuard AI.
"""
import os

SAMPLE_ORDER_TEXT = """IN THE HIGH COURT OF SINDH AT KARACHI
(Constitutional Jurisdiction)

Constitution Petition No. D - 2849 of 2026

1. M/s Orient Textiles Ltd.,
   Plot No. 42, Sector 15, Korangi Industrial Area, Karachi.
                                                          ..... Petitioner
                                VERSUS
1. Province of Sindh through Secretary Finance, Karachi.
2. Sindh Revenue Board (SRB), through its Chairman, Karachi.
3. Assistant Commissioner (Unit-04), SRB, Karachi.
4. National Bank of Pakistan, Main Branch, Karachi.
                                                          ..... Respondents

Date of Hearing: 28th September 2026.
Before:
Mr. Justice Tariq Mehmood Jahangiri
Mr. Justice Arshad Hussain

ORDER / JUDGMENT

1. By this constitutional petition filed under Article 199 of the Constitution of the Islamic Republic of Pakistan, 1973, the Petitioner impugns notice of attachment dated 15.09.2026 issued by Respondent No. 3 under Section 66 of the Sindh Sales Tax on Services Act, 2011, whereby bank accounts of the petitioner have been frozen for recovery of alleged arrears amounting to PKR 30,000,000/-.

2. Learned counsel for the petitioner submits that the statutory appeal against the assessment order is already pending before the Commissioner (Appeals), SRB, along with a stay application. However, without deciding the said stay application, coercive measures have been initiated in flagrant violation of the principles laid down by the Hon'ble Supreme Court.

3. Conversely, learned counsel appearing on behalf of the Sindh Revenue Board vehemently contends that ample opportunities were provided to the petitioner to discharge their admitted liability, but they failed to deposit any portion of the assessed sales tax.

4. We have heard the learned counsel at length and perused the available record.

5. It is a well-settled principle of law that during the pendency of a statutory appeal, coercive recovery measures should not ordinarily be adopted in a manner that renders the remedy of appeal infructuous. However, the interest of the public exchequer must also be safeguarded.

6. In view of the above circumstances, with the consent of both sides, this petition is disposed of in the following terms:

7. The Petitioner (M/s Orient Textiles Ltd.) is directed to deposit 15% of the disputed demand (amounting to PKR 4,500,000/-) with the Nazir of this Court in the form of a Pay Order or Call Deposit within ten (10) days from today. Failing which, the interim relief granted herein shall stand automatically vacated without further notice to the petitioner, and respondents shall be at liberty to proceed in accordance with law.

8. Upon submission of the Nazir's compliance certificate confirming receipt of the aforesaid 15% deposit, Respondent No. 2 (Sindh Revenue Board) and Respondent No. 3 are strictly directed to immediately defreeze all commercial bank accounts of the petitioner within 24 hours, and refrain from adopting any coercive steps against the petitioner until the final decision of the pending appeal. If Respondent No. 2 fails to defreeze the accounts within the stipulated 24 hours, Contempt of Court proceedings under Article 204 of the Constitution shall be initiated against the Commissioner.

9. Respondent No. 1 and Respondent No. 2 shall submit their detailed parawise comments and counter-affidavit before the Court Registry within three (3) weeks of receipt of notice of this order, failing which ex-parte proceedings will be ordered and their right of reply shall be forfeited.

10. The Commissioner (Appeals), Sindh Revenue Board, is directed to decide the pending statutory appeal on merits within a period of thirty (30) days from the date of receipt of this order, after providing full opportunity of hearing to the petitioner.

11. The Court Office / Registrar is directed to list this matter on 04.11.2026 for compliance report by the Nazir.

Announced in open Court on this 28th day of September 2026.

                                                    (Justice Arshad Hussain)
                                                (Justice Tariq Mehmood Jahangiri)
"""

def save_sample_order():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    txt_path = os.path.join(output_dir, "sample_court_order.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_ORDER_TEXT)
    print(f"Sample order text saved at: {txt_path}")
    return txt_path

if __name__ == "__main__":
    save_sample_order()
