from rdflib import URIRef

from django.utils.safestring import mark_safe, SafeData

from humfrey.utils.namespaces import register as register_namespace, expand
from humfrey.utils.resource import register, Image

class Journal(object):
    template_name = 'doc/journal'
    
    @classmethod
    def _describe_patterns(cls):
        return [
            '%(n0)s frbr:part+ %(uri)s',
        ]
register(Journal, 'fabio:Journal')
    

class JournalArticle(object):
    template_name = 'doc/article'

    _ABSTRACT_URI = expand('fabio:Abstract')
    _REFERENCE_LIST_URI = expand('biro:REFERENCE_LIST')

    @classmethod
    def _describe_patterns(cls):
        return [
            '%(uri)s frbr:part %(n0)s . %(n0)s a fabio:Abstract',
            '%(uri)s frbr:part %(n0)s . %(n0)s a biro:ReferenceList ; collections:item %(n1)s',
            '%(uri)s pro:isRelatedToRoleInTime %(n0)s . %(n1)s pro:holdsRoleInTime %(n0)s',
            '%(n0)s frbr:part+ %(uri)s',
        ]
    @classmethod
    def _construct_patterns(cls):
        return [
            '%(uri)s cito:cites %(cited)s . %(cited)s a %(citedType)s ; dcterms:title %(citedTitle)s',
            '%(citedBy)s cito:cites %(uri)s . %(citedBy)s a %(citedByType)s ; dcterms:title %(citedByTitle)s',
            ('%(sup)s a %(supType)s ; frbr:part %(supPart)s ; dcterms:title %(supTitle)s', '%(sup)s frbr:part+ %(uri)s ; a %(supType)s ; frbr:part %(supPart)s . OPTIONAL { %(sup)s dcterms:title %(supTitle)s }'),
        ]

    def _part_by_type(self, type):    
        for part in self.all.frbr_part:
            if type in (t._identifier for t in part.all.rdf_type):
                return part
        return None

    abstract = property(lambda self:self._part_by_type(self._ABSTRACT_URI))
    reference_list = property(lambda self:self._part_by_type(self._REFERENCE_LIST_URI))

    @property
    def identifiers(self):
        ret = []
        if self.prism_doi:
            ret.append(('DOI', self.prism_doi, 'http://dx.doi.org/%s' % self.prism_doi))
        if self.fabio_hasPubMedId:
            ret.append(('PMID', self.fabio_hasPubMedId, 'http://www.ncbi.nlm.nih.gov/pubmed/%s' % self.fabio_hasPubMedId))
        if self.fabio_hasPubMedCentralId:
            ret.append(('PMC', self.fabio_hasPubMedCentralId, 'http://www.ncbi.nlm.nih.gov/sites/ppmc/articles/PMC%s/' % self.fabio_hasPubMedCentralId))
        return ret


register(JournalArticle, 'fabio:Article', 'fabio:JournalArticle', 'fabio:Expression')

class RoleInTime(object):
    _LABEL_MAP = {
        'pro:author': 'authorship of %s',
        'pro:editor': 'editorship of %s',
        'pro:peer-reviewer': 'peer-reviewing of %s',
        'pro:translator': 'role as translator of %s',
    }
    _LABEL_MAP = dict((expand(qname), label_format) for qname, label_format in _LABEL_MAP.items())
    
    @property
    def label(self):
        role_type = self._LABEL_MAP.get(self.pro_withRole._identifier)
        if role_type:
            return role_type % self.pro_holdsRoleInTime_inv.rdfs_label
        else:
            return super(RoleInTime, self).label
    @classmethod

    def _describe_patterns(cls):
        return [
            '%(n0)s pro:isRelatedToRoleInTime %(uri)s',
            '%(n0)s pro:holdsRoleInTime %(uri)s',
        ]
register(RoleInTime, 'pro:RoleInTime')

class Person(object):
    template_name = 'doc/person'
    
    @classmethod
    def _describe_patterns(cls):
        return [
            '%(uri)s pro:isRelatedToRoleInTime %(n0)s',
            '%(n0)s dcterms:creator %(uri)s',
            '%(n0)s dcterms:contributor %(uri)s',
        ]
register(Person, 'foaf:Person')

class List(object):
    def __iter__(self):
        item = self.collections_firstItem
        while item:
            yield item
            item = item.collections_nextItem
register(List, 'biro:ReferenceList', 'collections:List')