from odoo import fields, models, api


class libros(models.Model):
    _inherit = ['portal.mixin','mail.thread','mail.activity.mixin'] 
    _name = 'libros'
    
    name = fields.Char('Nombre del libro', required=True,track_visibility='onchange')
    editorial  = fields.Char('Editorial', required=True, track_visibility='onchange')
    isbn  = fields.Char('ISBN',track_visibility='onchange')
    author_id = fields.Many2one('author',string='Author', required=True,track_visibility='onchange' )
    image = fields.Binary('Imagen',track_visibility='onchange')
    
    #aplica restricciones para que no se cree un articulo con el mismo nombre
    _sql_constraints=[("name_uniq","unique (name)","El nombre ya existe")]