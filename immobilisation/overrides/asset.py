from erpnext.assets.doctype.asset.asset import Asset
import frappe
from frappe import _
from erpnext.assets.doctype.asset_category.asset_category import get_asset_category_account

class CustomAsset(Asset):

    def before_submit(self):
        depreciation_start_date = self.finance_books[0].depreciation_start_date
        amount = self.get_first_year_depreciation()
        fy_doc = frappe.get_doc("Fiscal Year", 
            {
                "year_start_date" : ["<=", depreciation_start_date],
                "year_end_date" : [">=", depreciation_start_date],
            }
        )
        self.reevalutaion_details.clear()
        self.append(
            "reevalutaion_details",
            {
                "annee": fy_doc.name,
                "base": self.gross_purchase_amount,
                "dotation": amount[0].depreciation_amount,
                "ratio": 1,
                "date_traitement": frappe.utils.getdate(),
            }
        )

    def get_first_year_depreciation(self):
        return frappe.db.sql(
            """
            SELECT SUM(depreciation_amount) AS depreciation_amount
            FROM `tabDepreciation Schedule` ds INNER JOIN 
                (SELECT MIN(YEAR(schedule_date)) AS min_year FROM `tabDepreciation Schedule` WHERE parent = %s) t 
                ON YEAR(ds.schedule_date) = t.min_year
            WHERE parent = %s
            """, (self.name, self.name), as_dict=1
        )

    def get_complement_account(self,account):
        fixed_asset_account = get_asset_category_account(
            account, None, self.name, None, self.asset_category, self.company
        )
        if not fixed_asset_account:
            frappe.throw(
                _("Set {0} in asset category {1} for company {2}").format(
                    frappe.bold("Fixed Asset Account"),
                    frappe.bold(self.asset_category),
                    frappe.bold(self.company),
                ),
                title=_("Account not Found"),
            )
        return fixed_asset_account
        

    def make_complement_gl_entries(self,amount):
        gl_entries = []

        fixed_asset_account, cwip_account = self.get_complement_account('complement_sur_valeur'), self.get_cwip_account()


        gl_entries.append(
            self.get_gl_dict(
                {
                    "account": cwip_account,
                    "against": fixed_asset_account,
                    "remarks": self.get("remarks") or _("Accounting Entry for Asset"),
                    "posting_date": frappe.utils.getdate(),
                    "credit": amount,
                    "credit_in_account_currency": amount,
                    "cost_center": self.cost_center,
                },
                item=self,
            )
        )

        gl_entries.append(
            self.get_gl_dict(
                {
                    "account": fixed_asset_account,
                    "against": cwip_account,
                    "remarks": self.get("remarks") or _("Accounting Entry for Asset"),
                    "posting_date": frappe.utils.getdate(),
                    "debit": amount,
                    "debit_in_account_currency": amount,
                    "cost_center": self.cost_center,
                },
                item=self,
            )
        )

        if gl_entries:
            from erpnext.accounts.general_ledger import make_gl_entries

            make_gl_entries(gl_entries)
            #self.db_set("booked_fixed_asset", 1)

    def make_complement_depreciation_entries(self,amount):
        accumulated_depreciation_account, complement_sur_amortissement = self.get_complement_account('accumulated_depreciation_account'), self.get_complement_account('complement_sur_amortissement')

        depreciation_cost_center, depreciation_series = frappe.get_cached_value(
            "Company", self.company, ["depreciation_cost_center", "series_for_depreciation_entry"]
        )
        depreciation_cost_center = self.cost_center or depreciation_cost_center

        je = frappe.new_doc("Journal Entry")
        #je.voucher_type = "Depreciation Entry"
        #je.naming_series = depreciation_series
        je.company = self.company
        je.remark = "Complement of depreciation"
        je.posting_date = frappe.utils.getdate()
        #doc = frappe.get_doc("Asset", self.name)
        #doc_type = frappe.get_doctype('Asset')
        je.append(
            "accounts",
            {
                "account": complement_sur_amortissement,
                "reference_type": "Asset",
                "reference_name": self.name,
                "cost_center": depreciation_cost_center,
                "credit": amount,
                "credit_in_account_currency": amount,
            },
        )

        je.append(
            "accounts",
            {
                "account": accumulated_depreciation_account,
                "reference_type": "Asset",
                "reference_name": self.name,
                "debit": amount,
                "debit_in_account_currency": amount,
            },
        )
        if je:
            je.save()


    def make_complement_entries(self,amount, type, name, date):
        if type == 'base':
            debit_account, credit_amortissement = self.get_complement_account('complement_sur_valeur'), self.get_cwip_account()
        else :
            debit_account, credit_amortissement = self.get_complement_account('accumulated_depreciation_account'), self.get_complement_account('complement_sur_amortissement')

            depreciation_cost_center, depreciation_series = frappe.get_cached_value(
                "Company", self.company, ["depreciation_cost_center", "series_for_depreciation_entry"]
            )
            depreciation_cost_center = self.cost_center or depreciation_cost_center

        je = frappe.new_doc("Journal Entry")
        je.voucher_type = 'Depreciation Entry'
        je.company = self.company
        je.remark = "Complement sur Valeur Initiale" if type == 'base' else "Complement sur Ammortissements"
        je.posting_date = date
        je.cheque_no = name
        je.cheque_date = date
        je.multi_currency = 1 #a enlever apres
        if type == 'base':
            je.append(
                "accounts",
                {
                    "account": credit_amortissement,
                    "reference_type": "Asset",
                    "reference_name": self.name,
                    "credit": amount,
                    "credit_in_account_currency": amount,
                },
            )
        else :
            je.append(
                "accounts",
                {
                    "account": credit_amortissement,
                    "reference_type": "Asset",
                    "reference_name": self.name,
                    "cost_center": depreciation_cost_center,
                    "credit": amount,
                    "credit_in_account_currency": amount,
                },
            )

        je.append(
            "accounts",
            {
                "account": debit_account,
                "reference_type": "Asset",
                "reference_name": self.name,
                "debit": amount,
                "debit_in_account_currency": amount,
            },
        )
        if je:
            je.save()