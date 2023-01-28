
{
    'name': 'Modulo Libros',
    'version': '16.0.0',
    'author': 'YQUADIT',
    'website': 'http://www.quadit.mx',
    'license': 'AGPL-3',
    'summary': 'practica libros',
    'depends': ['mail','base','sale_management','account'],
    'data': [
        'views/view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
