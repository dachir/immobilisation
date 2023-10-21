# Copyright (c) 2023, Richard Amouzou and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ReevaluationAnnuelle(Document):

	def on_cancel(self):
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
				WHERE status IN ("Submitted","Partially Depreciated") AND docstatus = 1
				{condition}
			""".format(condition=cond), as_dict = 1
		)
		self.asset_details.clear()
		for a in assets:
			self.append("asset_details",{"asset": a.name})

	def on_submit(self):
		cond = ""
		if self.company : 
			cond += " AND asset_owner_company = '" + self.company + "'"
		if self.category : 
			cond += " AND asset_category = '" + self.category + "'"
		if self.debut : 
			cond += " AND available_for_use_date >= '" + self.debut + "'"
		if self.fin : 
			cond += " AND available_for_use_date <= '" + self.fin + "'"
		
		reev_list = frappe.db.sql(
			"""
				SELECT *
				FROM(
					SELECT ra.exercice,NOW() AS date_traitement, 1 AS docstatus, rb.parent, rb.base, rb.dotation,a.available_for_use_date, rd.debut, rd.fin, rd.ratio, 
					(rd.ratio - rb.ratio) * rb.base AS comp_base, (rd.ratio - rb.ratio) * rb.dotation AS comp_dotation,
					'reevalutaion_details' as parentfield, 'Asset' AS parenttype
					FROM `tabReevaluation Annuelle` ra INNER JOIN `tabReevaluation Asset Details` rad ON ra.name = rad.parent
						INNER JOIN `tabReevaluation Bien` rb ON rad.asset = rb.parent AND rb.idx = 1
						INNER JOIN `tabAsset` a ON a.name = rb.parent 
						INNER JOIN `tabRatio Details` rd ON ra.ratio = rd.parent AND a.available_for_use_date BETWEEN  rd.debut AND rd.fin
					WHERE ra.name = %s
				) AS t
			""",(self.name), as_dict = 1
		)

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
			as_doc.make_complement_entries(i.comp_base, 'base', self.name, self.posting_date)
			as_doc.make_complement_entries(i.comp_dotation, 'complement', self.name, self.posting_date)
			

