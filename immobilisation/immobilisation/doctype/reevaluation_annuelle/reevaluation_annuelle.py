# Copyright (c) 2023, Richard Amouzou and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.journal_entry.journal_entry import make_reverse_journal_entry

class ReevaluationAnnuelle(Document):

	def on_cancel(self):
		"""
		for i in self.asset_details:
			asset_doc = frappe.get_doc("Asset", i.asset)   
			reev = frappe.db.sql(
				
				SELECT name
				FROM `tabReevaluation Bien`
				WHERE annee = %s AND parent = %s
				LIMIT 1
				
				, (self.annee, i.asset), as_dict=1
			)
			reev_doc = frappe.get_doc("Reevaluation Bien", reev[0].name)
			asset_doc.remove(reev_doc)
			asset_doc.save()
		"""


		jes = frappe.db.get_list("Journal Entry",["name"],  {"cheque_no" : self.name})
		for j in jes:
			jv = frappe.get_doc("Journal Entry", j.name)
			jv.cancel()
	
	@frappe.whitelist()
	def get_assets(self):
		cond = ""
		if self.company : 
			cond += " AND asset_owner_company = '" + self.company + "'"
		if self.category : 
			cond += " AND asset_category = '" + self.category + "'"
		if self.debut : 
			cond += " AND available_for_use_date >= '" + self.debut + "'"
		if self.fin : 
			cond += " AND available_for_use_date <= '" + self.fin + "'"
		
		assets = frappe.db.sql(
			"""
				SELECT *
				FROM tabAsset
				WHERE status IN ("Submitted","Partially Depreciated","Fully Depreciated") AND docstatus = 1
				{condition}
			""".format(condition=cond), as_dict = 1
		)
		self.asset_details.clear()
		for a in assets:
			self.append("asset_details",{"asset": a.name})

	def on_submit(self):
		for i in self.asset_details:
			old_valeur_reevalue = 0
			old_amortissement_reevalue = 0
			old_complement_amortissement = 0

			exo_list = frappe.db.sql(
				"""
					SELECT MAX(ra.exercice) AS exercice
					FROM `tabReevaluation Asset Details` rad INNER JOIN `tabReevaluation Annuelle` ra ON rad.parent = ra.name 
					WHERE ra.docstatus = 1  AND rad.asset = %(asset)s AND ra.exercice < %(exercice)s
				""",{"asset": i.asset, "exercice": self.exercice}, as_dict = 1
			)
			if exo_list[0].exercice != None:
				old_exercice = exo_list[0].exercice

				old_list = frappe.db.sql(
					"""
						SELECT rad.*
						FROM `tabReevaluation Asset Details` rad INNER JOIN `tabReevaluation Annuelle` ra ON rad.parent = ra.name 
						WHERE ra.docstatus = 1 AND rad.asset = %(asset)s AND ra.exercice = %(exercice)s
					""",{"asset": i.asset, "exercice": old_exercice}, as_dict = 1
				)
				old_valeur_reevalue = old_list[0].valeur_reevalue
				old_amortissement_reevalue = old_list[0].amortissement_reevalue
				old_complement_amortissement = old_list[0].complement_amortissement
			else:
				old_list = frappe.db.sql(
					"""
						SELECT SUM(d.depreciation_amount)  AS depreciation_val, MAX(a.gross_purchase_amount) AS valeur_init
						FROM tabAsset a INNER JOIN `tabDepreciation Schedule` d ON a.name = d.parent
						INNER JOIN `tabReevaluation Asset Details` rad ON rad.asset = a.name
						INNER JOIN `tabReevaluation Annuelle` ra ON rad.parent = ra.name AND YEAR(d.schedule_date) <= ra.exercice
						INNER JOIN `tabRatio Details` rd ON ra.ratio = rd.parent AND a.available_for_use_date BETWEEN  rd.debut AND rd.fin
					WHERE ra.name = %(name)s AND a.name = %(asset)s AND ra.docstatus = 1
				""",{"name":self.name, "asset": i.asset}, as_dict = 1
				)

				old_valeur_reevalue = old_list[0].valeur_init
				old_amortissement_reevalue = old_list[0].depreciation_val

				#frappe.throw(str(old_list[0].valeur_init))
			#frappe.throw(str(old_valeur_reevalue) + "||" + str(old_amortissement_reevalue))

			reev_list = frappe.db.sql(
				"""
					SELECT SUM(d.depreciation_amount * rd.ratio)  AS depreciation_reeval, MAX(rd.ratio) AS ratio, MAX(a.gross_purchase_amount)* rd.ratio AS valeur_reeval,
						SUM(d.depreciation_amount)  AS depreciation_amount
					FROM tabAsset a INNER JOIN `tabDepreciation Schedule` d ON a.name = d.parent
						INNER JOIN `tabReevaluation Asset Details` rad ON rad.asset = a.name
						INNER JOIN `tabReevaluation Annuelle` ra ON rad.parent = ra.name AND YEAR(d.schedule_date) <= ra.exercice
						INNER JOIN `tabRatio Details` rd ON ra.ratio = rd.parent AND a.available_for_use_date BETWEEN  rd.debut AND rd.fin
					WHERE ra.name = %(name)s AND a.name = %(asset)s AND ra.docstatus = 1
				""",{"name":self.name, "asset": i.asset}, as_dict = 1
			)
			i.valeur_reevalue = reev_list[0].valeur_reeval
			i.amortissement_reevalue = reev_list[0].depreciation_reeval
			i.ratio = reev_list[0].ratio
			i.dotation_periode = reev_list[0].depreciation_amount

			#frappe.throw(str( reev_list[0].valeur_reeval) + "||" + str(reev_list[0].depreciation_reeval))

			frappe.db.set_value('Reevaluation Asset Details', i.name, 'valeur_reevalue', reev_list[0].valeur_reeval)
			frappe.db.set_value('Reevaluation Asset Details', i.name, 'amortissement_reevalue', reev_list[0].depreciation_reeval)
			frappe.db.set_value('Reevaluation Asset Details', i.name, 'ratio', reev_list[0].ratio)
			frappe.db.set_value('Reevaluation Asset Details', i.name, 'dotation_periode', reev_list[0].depreciation_amount)


			if exo_list[0].exercice == None:
				comp_base = i.valeur_reevalue - old_valeur_reevalue
				comp_dotation = i.amortissement_reevalue - old_amortissement_reevalue
			else:
				depreciation_amount = reev_list[0].depreciation_amount
				ratio = reev_list[0].ratio
				comp_base = i.valeur_reevalue - old_valeur_reevalue
				comp_dotation = (i.amortissement_reevalue - depreciation_amount) - old_complement_amortissement

			i.complement_valeur = comp_base
			i.complement_amortissement = comp_dotation

			frappe.db.set_value('Reevaluation Asset Details', i.name, 'complement_valeur', comp_base)
			frappe.db.set_value('Reevaluation Asset Details', i.name, 'complement_amortissement', comp_dotation)
			


			as_doc = frappe.get_doc('Asset', i.asset)

			if comp_base > 0 :
				as_doc.make_complement_entries(comp_base, 'base', self.name, self.posting_date)
			if comp_dotation > 0 :
				as_doc.make_complement_entries(comp_dotation, 'complement', self.name, self.posting_date)


		




		"""
		for i in reev_list:
			as_doc = frappe.get_doc('Asset', i.parent)
			#rb_doc = frappe.get_doc("Reevaluation Bien", {"parent" : i.parent})
			rb_doc = frappe.new_doc('Reevaluation Bien')
			rb_doc.annee = i.exercice
			rb_doc.base = i.comp_base
			rb_doc.dotation = i.comp_dotation
			rb_doc.ratio = i.ratio
			rb_doc.date_traitement = i.date_traitement
			rb_doc.docstatus = as_doc.docstatus
			rb_doc.parent = i.parent
			rb_doc.parentfield = i.parentfield
			rb_doc.parenttype  = i.parenttype
			rb_doc.idx = len(as_doc.reevalutaion_details) + 1

			rb_doc.save()

			if as_doc.last_reevaluation:
				journal_entries = frappe.db.get_list("Journal Entry", fields=["*"], filters={"cheque_no": as_doc.last_reevaluation, "docstatus" : 1})
				for je in journal_entries:
					rev = make_reverse_journal_entry(je.name)
					rev.posting_date = frappe.utils.getdate()
					rev.cheque_no = self.name
					rev.cheque_date = je.posting_date
					rev.user_remark = je.name
					rev.save()

			if i.comp_base > 0 :
				as_doc.make_complement_entries(i.comp_base, 'base', self.name, self.posting_date)
			if i.comp_dotation > 0 :
				as_doc.make_complement_entries(i.comp_dotation, 'complement', self.name, self.posting_date)

			
			frappe.db.set_value('Asset', i.parent, 'last_reevaluation', self.name)
		"""	

