from django.conf import settings
import imp
import xlwt
import csv
import cStringIO as StringIO
from django.http import HttpResponse


def getQuerySet(job):
    '''
    Given a job record, return a spatialite queryset representing the job results.
    '''
    db_id='{0}'.format(job.pk)
    if db_id not in settings.DATABASES:
        settings.DATABASES[db_id]={'ENGINE': 'django.contrib.gis.db.backends.spatialite', 
                                   'NAME': job.sqlite_db.path }
    model=imp.load_source('%s.models' % (job.pk,),job.model.path)
    qs=model.Results.objects.using(db_id).all()
    return qs

def stream_csv(job):
    csvfile=StringIO.StringIO()
    csvwriter=csv.writer(csvfile)
    qs=getQuerySet(job)
    row=qs[0]
    db_map=[(field.db_column or field.name, field.name) for
             field in row._meta.fields]
    
    def read_and_flush():
        csvfile.seek(0)
        data=csvfile.read()
        csvfile.seek(0)
        csvfile.truncate()
        return data
    
    def data():
        # Output the CSV headings
        csvwriter.writerow([i[0] for i in db_map])
        for row in qs:
            csvwriter.writerow([getattr(row, mf) for dbf, mf in db_map])
        data=read_and_flush()
        yield data
        
    response=HttpResponse(data(), mimetype="text/csv")
    response.streaming=True
    response['Content-Disposition']="attachment; filename=results.csv"
    return response

def stream_xls(job):
    qs=getQuerySet(job)
    row=qs[0]
    db_map=[(field.db_column or field.name, field.name) for
             field in row._meta.fields]
    font0 = xlwt.Font()
    font0.name = 'Times New Roman'
    font0.colour_index = 2
    font0.bold = True
    font1=xlwt.Font()
    font1.name='Times New Roman'
    style0 = xlwt.XFStyle()
    style0.font = font0
    style1 = xlwt.XFStyle()
    style1.font = font1
    wb = xlwt.Workbook()
    ws = wb.add_sheet('NMTK Results')
    rowid=0
    for i, v in enumerate(db_map):
        ws.write(rowid, i, v[0], style0)
    for row in qs:
        rowid += 1
        for i, v in enumerate(db_map):
            ws.write(rowid, i, getattr(row, v[1]), style1)
    
    response=HttpResponse(mimetype="application/ms-excel")
    response.streaming=True
    response['Content-Disposition']="attachment; filename=results.xls"
    wb.save(response)
    return response