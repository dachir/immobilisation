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
		# Initialize conditions list
		conditions = []
		parameters = []

		# Add conditions based on user input
		if self.company:
			conditions.append("a.asset_owner_company = %s")
			parameters.append(self.company)

		if self.category:
			conditions.append("a.asset_category = %s")
			parameters.append(self.category)

		if self.debut:
			conditions.append("a.available_for_use_date >= %s")
			parameters.append(self.debut)

		if self.fin:
			conditions.append("a.available_for_use_date <= %s")
			parameters.append(self.fin)

		# Combine conditions into a single string
		cond = " AND " + " AND ".join(conditions) if conditions else ""

		# SQL Query
		query = f"""
			SELECT a.*, rd.exercice
			FROM `tabAsset` a
			LEFT JOIN (
				SELECT rad.*, ra.exercice
				FROM `tabReevaluation Asset Details` rad
				INNER JOIN `tabReevaluation Annuelle` ra ON rad.parent = ra.name
				WHERE ra.exercice = %s AND ra.docstatus = 1
			) rd ON rd.asset = a.name
			WHERE a.status IN ("Submitted", "Partially Depreciated", "Fully Depreciated")
			AND a.docstatus = 1 AND rd.asset IS NULL
			{cond}
		"""

		# Add exercice to parameters
		parameters.insert(0, self.exercice)

		# Execute the query
		assets = frappe.db.sql(query, parameters, as_dict=1)

		# Clear and append results
		self.asset_details.clear()
		for a in assets:
			self.append("asset_details", {"asset": a.name})


	def on_submit(self):
		for i in self.asset_details:
			old_valeur_reevalue = 0
			old_amortissement_reevalue = 0
			old_complement_amortissement = 0
			old_ratio = 0
			old_exercice = 0

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
				old_amortissement_reevalue = old_list[0].amortissement_reevalue * old_list[0].ratio
				old_complement_amortissement = old_list[0].complement_amortissement
				old_ratio = old_list[0].ratio
			else:
				old_list = frappe.db.sql(
					"""
						SELECT SUM(d.depreciation_amount)  AS depreciation_val, MAX(a.gross_purchase_amount) AS valeur_init, MAX(ra.ratio) AS ratio
						FROM tabAsset a INNER JOIN `tabDepreciation Schedule` d ON a.name = d.parent
						INNER JOIN `tabReevaluation Asset Details` rad ON rad.asset = a.name
						INNER JOIN `tabReevaluation Annuelle` ra ON rad.parent = ra.name AND YEAR(d.schedule_date) <= ra.exercice
						INNER JOIN `tabRatio Details` rd ON ra.ratio = rd.parent AND a.available_for_use_date BETWEEN  rd.debut AND rd.fin
					WHERE ra.name = %(name)s AND a.name = %(asset)s AND ra.docstatus = 1
				""",{"name":self.name, "asset": i.asset}, as_dict = 1
				)

				old_valeur_reevalue = old_list[0].valeur_init
				old_amortissement_reevalue = old_list[0].depreciation_val
				old_ratio = old_list[0].ratio

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


			#i.valeur_reevalue = reev_list[0].valeur_reeval
			#i.amortissement_reevalue = reev_list[0].depreciation_reeval
			#i.ratio = reev_list[0].ratio
			#i.dotation_periode = reev_list[0].depreciation_amount

			#frappe.throw(str( reev_list[0].valeur_reeval) + "||" + str(reev_list[0].depreciation_reeval))

			valeur_reeval = 0
			depreciation_reeval = 0
			ratio = 0
			depreciation_amount = 0

			if reev_list[0].ratio == None:
				if old_exercice == 0:
					continue
				else:
					dep_list = frappe.db.sql(
						"""
							SELECT SUM(depreciation_amount) AS depreciation_amount, Count(*) AS nb
							FROM `tabDepreciation Schedule`
							WHERE YEAR(schedule_date) <= %(exercice)s AND parent =%(asset)s
						""",{"exercice":self.exercice, "asset": i.asset}, as_dict = 1
					)
					valeur_reeval = old_valeur_reevalue
					depreciation_reeval = dep_list[0].depreciation_amount * old_ratio
					ratio = old_ratio
					depreciation_amount = dep_list[0].depreciation_amount
			else:
				valeur_reeval = reev_list[0].valeur_reeval
				depreciation_reeval = reev_list[0].depreciation_reeval
				ratio = reev_list[0].ratio
				depreciation_amount = reev_list[0].depreciation_amount



			i.valeur_reevalue = valeur_reeval
			i.amortissement_reevalue = depreciation_reeval
			i.ratio = ratio
			i.dotation_periode = depreciation_amount

			frappe.db.set_value('Reevaluation Asset Details', i.name, 'valeur_reevalue', valeur_reeval)
			frappe.db.set_value('Reevaluation Asset Details', i.name, 'amortissement_reevalue', depreciation_reeval)
			frappe.db.set_value('Reevaluation Asset Details', i.name, 'ratio', ratio)
			frappe.db.set_value('Reevaluation Asset Details', i.name, 'dotation_periode', depreciation_amount)


			if exo_list[0].exercice == None:
				comp_base = valeur_reeval - old_valeur_reevalue
				comp_dotation = depreciation_reeval - old_amortissement_reevalue
			else:
				#depreciation_amount = depreciation_amount
				#ratio = ratio
				comp_base = valeur_reeval - old_valeur_reevalue
				comp_dotation = (depreciation_reeval - depreciation_amount) - old_complement_amortissement

			i.complement_valeur = comp_base
			i.complement_amortissement = comp_dotation

			frappe.db.set_value('Reevaluation Asset Details', i.name, 'complement_valeur', comp_base)
			frappe.db.set_value('Reevaluation Asset Details', i.name, 'complement_amortissement', comp_dotation)
			


			as_doc = frappe.get_doc('Asset', i.asset)

			if comp_base > 0 :
				as_doc.make_complement_entries(comp_base, 'base', self.name, self.posting_date)
			if comp_dotation > 0 :
				as_doc.make_complement_entries(comp_dotation, 'complement', self.name, self.posting_date)


			frappe.db.set_value('Asset', i.parent, 'last_reevaluation', self.name)
			frappe.db.set_value('Asset', i.parent, 'last_ratio', ratio)

			"""
			rb_doc = frappe.new_doc('Reevaluation Bien')
			rb_doc.annee = self.exercice
			rb_doc.dotation_periode = reev_list[0].depreciation_amount
			rb_doc.valeur_reevaluee = reev_list[0].valeur_reeval
			rb_doc.amortissement_reevalue = reev_list[0].depreciation_amount
			rb_doc.complement_valeur = comp_base
			rb_doc.complement_amortissement = comp_dotation
			rb_doc.ratio = reev_list[0].ratio
			#rb_doc.date_traitement = i.date_traitement
			rb_doc.docstatus = as_doc.docstatus
			rb_doc.parent = i.asset
			rb_doc.parentfield = "reevalutaion_details"
			rb_doc.parenttype  = "Asset"
			rb_doc.idx = len(as_doc.reevalutaion_details) + 1

			rb_doc.save()

			frappe.db.set_value('Asset', i.parent, 'last_reevaluation', self.name)
			"""
