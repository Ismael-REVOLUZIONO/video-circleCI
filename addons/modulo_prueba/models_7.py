from odoo import  api,fields,models, exceptions

class academia_calificacion(models.Model):
    _name = "academia.calificacion"
    _descripcion = "calificacion del estudiante"
    
    name = fields.Many2one('academia.materia','Materia')
    calificacion = fields.Float('calificacion',digits=(3,2))
    student_id = fields.Many2one('academia.student','ID Ref')
    
    
    @api.constrains('calificacion')
    def _check_calificacion(self):
        for record in self:
            if record.calificacion < 5 or record.calificacion>10:
                raise exceptions.ValidationError("calificacion debe ser mayor a 5 y menos a 10")
            

class academia_materia(models.Model):
    _name = "academia.materia"
    _description = "Materias"
    name = fields.Char('Nombre')
    
    _sql_constraints = [('name_uniq','unique(name)',
                        'El nombre de la materia nose puede repetir')]