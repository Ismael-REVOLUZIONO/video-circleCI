# -*- coding: utf-8 -*-
from odoo import _, api,fields,models, exceptions

class make_student_invoice(models.TransientModel):
    _name = 'make.student.invoice'
    _description = 'asistente para generar facturas'
    
    journal_id = fields.Many2one('account.journal', 'Diario',domain="[('type','=','sale')]")
    
    def make_invoices(self):
        active_ids = [self._context['active_ids']]
        category_obj = self.env['product.category']
        category_id = category_obj.search([('name','=','Facturacion Colegiatura')])
        
        for student_id in active_ids:
            student_br=self.env['academia.student'].search([('id','=',student_id)])
            if student_br.state in ('draft','cancel'):
                raise exceptions.ValidationError('no puedes generar una factura para un estudiante expulsado o en borrador')
                return False
            if category_id:
                product_obj=self.env['product.product']
                products = product_obj.search([('categ_id','=',category_id.id)])
                
                invoice_obj=self.env['account.move']
                partner_br=self.env['res.partner'].search([('student_id','=',student_br.id)])
                if partner_br:
                    partner_id=partner_br[0].id 
                    invoice_lines=[]
                    for product in products:
                        xline = (0,0,{
                            'product_id':product.id,
                            'price_unit':product.list_price,
                            'quantity':1,
                            'account_id':product.categ_id.property_account_income_categ_id.id,
                            'name':product.name+"["+str(product.default_code)+"]",
                            })
                        invoice_lines.append(xline)
                        vals = {
                        'partner_id':partner_id,
                        'invoice_payment_term_id':7,
                        'move_type':'out_invoice',
                        'invoice_line_ids':invoice_lines,
                        }
                        invoice_id=self.env['account.move'].create(vals)
                        invoice_list=[x.id for x in student_br.invoice_ids]
                        invoice_list.append(invoice_id.id)
                        student_br.write({
                            'invoice_ids':[(6,0, invoice_list)]
                        })
                        return True
        

class res_partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    
    company_type = fields.Selection(selection_add=[('is_school','Escuela'),('student','Estudiante')])
    student_id = fields.Many2one("academia.student",string="student")
    
class academia_materia_list(models.Model):
    _name = "academia.materia.list"
    grado_id = fields.Many2one('academia.grado','ID referencia')
    materia_id = fields.Many2one('academia.materia','Materia',required=True)
    
class academia_grado(models.Model):
    _name = "academia.grado"
    _description = 'MOdelo de los grados de la materia que tiene la escuela'    
    
    @api.depends('name','group')
    def calculate_name(self):
        for record in self:
            complete_name=record.name+ " - " + record.group
            record.complete_name = complete_name
    _rec_name = 'complete_name'
    
    name = fields.Selection([
        ('1','Primero'),
        ('2','segundo'),
        ('3','tercero'),
        ('4','cuarto'),
        ('5','quinto'),
        ('6','sexto'),
    ],'Grado',required=True)
    group = fields.Selection([
        ('a','A'),
        ('b','B'),
        ('c','C'),
    ], 'Grupo',required=True)
    
    materia_ids = fields.One2many('academia.materia.list','grado_id','Materias')
    complete_name = fields.Char("nombre completo",size=128, compute="calculate_name",store=True)

class academia_student(models.Model):
    _inherit = ['portal.mixin','mail.thread','mail.activity.mixin']
    _name = "academia.student"
    _description = "gestion de estudiante"
    
    @api.model
    def _get_school_default(self):
        school_id=self.env['res.partner'].search([('name','=','My Company')])
        return school_id
    
    @api.depends('calificaciones_id')
    def calcular_promedio(self):
        acum = 0.0
        if len(self.calificaciones_id)>0:
            for xcal in self.calificaciones_id:
                acum += xcal.calificacion
                if acum:
                    self.promedio = acum/len(self.calificaciones_id)
        else:
            self.promedio=0.0
            
    
    @api.depends('invoice_ids')
    def calcular_amount(self):
        acum = 0.0
        for xcal in self.invoice_ids:
            acum += xcal.amount_total
            if acum:
                self.amount_invoice=acum
        
    name = fields.Char("Nombre",size=128, required=True, track_visibility='onchange')
    last_name= fields.Char("Apellido", size=128, required=True)
    photo = fields.Char("Fotografia")
    create_date = fields.Datetime("Fecha de creacion",readonly=True)
    curp = fields.Char("CURP",size=18,copy=False)
    note = fields.Html("Comentarios")
    state = fields.Selection([
        ('draft',"borrador"),
        ('process',"en proceso"),
        ('done',"egresado"),
        ('cancel',"expulsado")
    ],"Estado", default="draft")
    active = fields.Boolean("Activo",default = True)
    age = fields.Integer("Edad")
    
    partner_id = fields.Many2one('res.partner','Escuela', default=_get_school_default)
    country = fields.Many2one('res.country','Pais', related='partner_id.country_id')
    calificaciones_id = fields.One2many(
        'academia.calificacion',
        'student_id',
        'calificaciones'
    )
    invoice_ids = fields.Many2many('account.move',
                                    'student_invoice_rel',
                                    'student_id','journal_id',
                                    'Facturas')
    
    grado_id = fields.Many2one('academia.grado','Grado')
    promedio  = fields.Float('Promedio',digits=(3,2),compute="calcular_promedio")
    amount_invoice  = fields.Float('Monto Facturado',digits=(14,2),compute="calcular_amount",store=True)
    
    @api.onchange('grado_id')
    def onchange_grado(self):
        calificaciones_list = []
        for materia in self.grado_id.materia_ids:
            xval = (0,0,{
                'name':materia.materia_id.id,
                'calificacion':5
                })
            calificaciones_list.append(xval)
        self.update({'calificaciones_id':calificaciones_list})
    
    @api.constrains('curp')
    def _check_lines(self):
        if len(self.curp)<18:
            raise exceptions.ValidationError("CURP debe ser de 18 caracteres")
        
    
    @api.model
    def create(self, values):
        if values['name']:
            nombre = values['name']
            exist_ids = self.env['academia.student'].search([('name','=',self.name)])
            if exist_ids:
                values.update({
                    'name':values['name']+"(copia)",
                    })
        res = super(academia_student, self).create(values)
        partner_obj = self.env['res.partner']
        vals_to_partner={
            'name': res['name']+" "+res['last_name'],
            'company_type': 'student',
            'student_id': res['id'],
            }
        print(vals_to_partner)
        partner_id = partner_obj.create(vals_to_partner)
        print("===>partner_id", partner_id)
        return res
    
    def unlink(self):
        partner_obj = self.env['res.partner']
        partner_ids = partner_obj.search([('student_id','in',self.ids)])
        print("Partner ##### >>>>>",partner_ids)
        if partner_ids:
            for partner in partner_ids:
                partner.unlink()
                res=super(academia_student,self).unlink()
                return res
            
    def confirm(self):
        self.state='process'
        return True
    
    def cancel(self):
        self.state='cancel'
        return True
    
    def done(self):
        self.state='done'
        return True
    
    def draft(self):
        self.state='draft'
        return True
    
    def generarFactura(self):
        return{
            'name':'Generacion facturas',
            'res_model':'make.student.invoice',
            'type':'ir.actions.act_window',
            'view_id':self.env.ref('modulo_prueba.wizard_student_invoice').id,
            'view_mode':'form',
            'view_type':'form',
            'target':'new',
            'key2':"client_action_multi",
            'context':{'active_ids':self.id}
            
        }