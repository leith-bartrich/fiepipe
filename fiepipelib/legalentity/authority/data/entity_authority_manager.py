import fiepipelib.locallymanagedtypes
from fiepipelib.legalentity.authority.data.entity_authority import LegalEntityAuthority, FromJSONData, ToJSONData
import typing

class LegalEntityAuthorityManager(
    fiepipelib.locallymanagedtypes.data.abstractmanager.AbstractUserLocalTypeManager[LegalEntityAuthority]):
    """Manages the state of entities over which this user has created authority.  Such entities
    can then be registered for use on this system, or other systems that trust this system to have
    authority over the entity.

    It's important to note that a user is always capable of creating authority
    for any FQDN they wish.  One can pretend to be anyone in their own computer system.
    But of course, that
    doesn't grant them access to the true FQDN owner's identity outside their own computer system.
    Rather, they
    are creating a compartmentalized and independent entity that may be rejected by the rest of the world as being illegitimate.

    The difference between a legitimate member of an entity creating a fully disconnected
    and ad-hoc compartment for working within that entity, and a malicious individual
    doing the same, is nearly impossible to discern within the computer system because
    the administrator of that system can always force the software to make the wrong decision.  One must assume
    that any digital rights managment systems can be overridden by the administrator of the
    malicious system as well.
    However we need to allow the former and protect against the latter.

    The actual decision point therefore, is the point of data migration.  Either automated
    or manual.  In either case, the question is: "Do you trust the source of the data you are
    migrating into your compartment?"  The answer can come in many forms.  Usually, based on
    physical security in the end.
    e.g. The person bringing you the data is an actual trusted
    employee who has a
    legitimate reason and authorization for migrating data from an ad-hoc setup.
    e.g. The machine that is pushing
    data was authorized to do so when it was configured by an authorized administrator by installing a
    private key, that has not been revoked.

    Similarly, parralel, fully air-gapped and compartmentalized entities created by the FQDN
    might be desirable in high security environments.  And similarly, the security mechanisms
    center around data migration in the same way.

    fiepipe maintains the idea of multiple compartments within a FQDN on a system.  However, such
    compartments are lower security than actual parallel, fully air-gapped compartments.  We call the
    lower security compartments: containers.  Some might see them as simlar to 'projects' in other
    digital asset managment and workflow systems.  Though we use a more generic term here becasue
    not all compartmentalized data is project based.  It might be department based.  Or based on
    fiscal year, for example.

    The provisioning of extremely high security compartments starts here at the legal entity authority
    level, when an
    individual legitimately provisions an independent FQDN entity in the computer system,
    in which to create such a high security compartment.

    In the extreme, the legal entity (company) has a parallel facility and staff who operate a fully
    compartmentalized set of containers.  The less secure staff might not even know about the existence of
    the legitimate, but compartmentalized facility, staff and their projects and operations.  In that case,
    you have a completely
    different set of keys for the indepdendently provisioned FQDN.  Data from the high security compartment might
    migrate to lower security some day.  But that will require that the higher security data be migrated (declassified).
    And the people doing the ingest side of the migration need to be able to trust that whomever is delivering the
    data, is legitimate.  As such, the digital security is only maintained by the physical security.  Which is the correct
    way to handle redaction and declassification in highly secure scenarios.
    """

    def FromJSONData(self, data):
        return FromJSONData(data)

    def ToJSONData(self, item):
        return ToJSONData(item)

    def GetManagedTypeName(self):
        return "authored_legal_entity"

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("fqdn", "text"))
        return ret

    def GetPrimaryKeyColumns(self):
        return ["fqdn"]

    def DeleteByFQDN(self, fqdn):
        self._Delete("fqdn", fqdn)

    def GetByFQDN(self, fqdn) -> typing.List[LegalEntityAuthority]:
        return self._Get([("fqdn", fqdn)])