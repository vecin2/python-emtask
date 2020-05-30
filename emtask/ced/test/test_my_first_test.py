import lxml.etree as ET
import pytest

from emtask.ced import cedobject_factory
from emtask.ced.nubia_commands.commands import rewire_verb
from emtask.ced.tool import CED
from emtasktest.testutils import sample_project


class FakeConnector(object):
    """docstring for FakeConnector"""

    def __init__(
        self,
        server=None,
        user=None,
        password=None,
        database=None,
        port=None,
        dbtype=None,
        mock_connection=None,
    ):
        self.server = server
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.dbtype = dbtype
        self._valid_connection = {}
        self.mock_connection = mock_connection
        self._connection = None
        self._rows_to_return = None

    def with_connection_details(self, **kwargs):
        self._valid_connection = dict(**kwargs)

        return self

    def fetch_returns(self, rows):
        self._rows_to_return = rows

    def connect(self):
        if self._assert_valid_connection():
            self._connection = FakeConnection(
                self.server, self.user, self.password, self.database, port=self.port
            )
        self._connection.set_cursor(FakeCursor(self._rows_to_return))

        return self._connection

    def _assert_valid_connection(self):
        self.mock_connection.assert_called_once_with(
            self._valid_connection["database_host"],
            self._valid_connection["database_user"],
            self._valid_connection["database_pass"],
            self._valid_connection["database_name"],
            self._valid_connection["database_port"],
            self._valid_connection["database_type"],
        )

        return True

        return self.server == self._valid_connection["server"]


class FakeConnection(object):
    def __init__(self, server=None, user=None, password=None, database=None, port=None):
        self.server = server
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self._cursor = None

    def cursor(self):
        return self._cursor

    def set_cursor(self, cursor):
        self._cursor = cursor


class FakeCursor(object):

    """Docstring for FakeCursor. """

    def __init__(self, rows):
        """TODO: to be defined. """
        self.column_names_to_return = rows[0]
        self.rows_to_return = rows[1:]
        self.description = []
        self.rows = None

    def execute(self, query):
        self.row = self.rows_to_return[0]
        self.rows = self.rows_to_return

        for column_name in self.column_names_to_return:
            self.description.append([column_name])

    def __iter__(self):
        return self.rows.__iter__()

    def __next__(self):
        return self.rows.__next__()


@pytest.fixture
def fake_connector(mocker):
    """Returns an instance of FakeConnector when invoked within the module specified.
    FakeConnector uses the mock to assert that connection details match
    with those expected
    """
    mock = mocker.patch("emtask.database.Connector", autospec=True)
    fake_connector = FakeConnector(mock_connection=mock)
    mock.return_value = fake_connector
    yield fake_connector


@pytest.fixture
def createsql_cmd(mocker):
    createsql_cmd = mocker.patch("emtask.sql.tasks.CreateSQLTaskCommand")
    createsql_cmd.return_value = createsql_cmd
    yield createsql_cmd


# if testfilesystem.exists():
#    shutil.rmtree(testfilesystem)


def testing_with_mock(fake_connector, createsql_cmd, autospec=True):
    """Test it computes entity_keyname and verb_name from current_path
       and it calls rewire_verb sql template with correct parameters"""
    rows = [
        ("ENTITY_KEYNAME", "NAME", "REPOSITORY_PATH"),
        ("Contact", "inlineView", "Contact.verbs.InlineView"),
    ]
    fake_connector.fetch_returns(rows)
    sample_project(db_connector=fake_connector)

    rewire_verb(
        current_path="Contact.Verbs.InlineView", new_path="PCContact.Verbs.InlineView"
    )

    template_values = {
        "entity_def_id": "Contact",
        "new_pd_path": "PCContact.Verbs.InlineView",
        "verb_name": "inlineView",
    }
    createsql_cmd.assert_called_once_with(
        template_name="rewire_verb.sql", template_values=template_values, run_once=True
    )
    createsql_cmd.run.assert_called_once()


@pytest.fixture
def ced():
    ced = CED(sample_project().get_repo())
    yield ced


def test_when_creating_new_process_save_and_reopen_they_match(ced):
    process_path = "PRJContact.Implementation.Contact.InlineContact"
    process = ced.new_process(process_path)
    process.save()

    assert ced.get_realpath(process_path).exists()
    assert_file_matches_process(ced, process_path, process)


def test_create_process_wrapper(ced):
    process_path = "PRJContact.Implementation.Contact.InlineContact"
    process = ced.new_process(process_path)
    process.add_field(of.make_field("String", "name1"))
    process.mark_as_parameter("name1")
    wrapper_path = "PRJContact.Implementation.Contact.InlineContactWrapper"
    wrapper_process = process.wrapper(wrapper_path)

    assert wrapper_path == wrapper_process.path
    wrapper_params = wrapper_process.get_parameters()
    process_params = wrapper_process.get_parameters()
    assert len(wrapper_params) == len(process_params)

    for i in range(len(wrapper_params)):
        assert_equal_node(process_params[i], wrapper_params[i])


def assert_equal_node(expected, actual):
    assert ET.tostring(expected) == ET.tostring(actual)


of = cedobject_factory


def test_add_all_basic_types_fields(ced):
    process = ced.new_process("Test.TestProcess")
    process.add_field(of.make_field("String", "name1"))
    process.add_field(of.make_field("Number", "referenceNo"))
    process.add_field(of.make_field("Integer", "streetNumber"))
    process.add_field(of.make_field("Float", "partialAmount"))
    # defaults to precision 42 and scale 1
    process.add_field(of.make_field("Decimal", "totalAmount"))
    process.add_field(of.make_field("Character", "oneLetter"))
    process.add_field(of.make_field("Date", "dob"))
    assert process.get_field("name1") is not None
    assert process.get_field("referenceNo") is not None
    assert process.get_field("streetNumber") is not None
    assert process.get_field("partialAmount") is not None
    assert process.get_field("totalAmount") is not None
    assert process.get_field("oneLetter") is not None
    assert process.get_field("dob") is not None
    # todo type Form


# <ObjectField
#    designNotes=""
#    isAggregate="false"
#    isAttribute="false"
#    name="aProcess">
#  <ObjectField_loc
#      locale="">
#    <Format />
#  </ObjectField_loc>
#  <TypeDefinitionReference
#      name="AProcess2"
#      nested="false" />
# </ObjectField>
def test_add_object_field(ced):
    childprocess = ced.new_process("Test.TestChildProcess")
    process = ced.new_process("Test.TestMainProcess")
    field = make_object_field("TestChildProcess")
    process.add_field(field)
    returned_field = process.get_field("childProcess")
    assert_equal_node(returned_field, field)


def make_object_field(name):
    field = of.make_field("Object", "childProcess")
    ET.SubElement(field, "TypeDefinitionReference", name=name, nested="false")

    return field


def test_add_parameters(ced):
    process = ced.new_process("Test.TestProcessParameter")
    process.add_field(cedobject_factory.make_field("String", "street"))
    process.add_field(cedobject_factory.make_field("Number", "streetNumber"))
    process.mark_as_parameter("street")
    process.mark_as_parameter("streetNumber")
    assert process.get_field("street") is not None
    assert "street" == process.get_parameters()[0].get("name")
    assert process.get_field("streetNumber") is not None
    assert "streetNumber" == process.get_parameters()[1].get("name")


def test_add_result(ced):
    process = ced.new_process("Test.TestProcessResult")
    process.add_field(cedobject_factory.make_field("String", "street"))
    process.add_field(cedobject_factory.make_field("Number", "streetNumber"))

    process.mark_as_result("street")
    process.mark_as_result("streetNumber")

    assert process.get_field("street") is not None
    assert "street" == process.get_results()[0].get("name")
    assert process.get_field("streetNumber") is not None
    assert "streetNumber" == process.get_results()[1].get("name")


def test_add_procedure(ced):
    process = ced.new_process("Test.TestProcessResult")
    process.add_general_procedure("setUp")

    process.save()

    procedure = process.get_procedure("setUp")
    assert procedure is not None
    assert "Test.TestProcessResult.setUp" == procedure.path


def test_add_procedure2(ced):
    procedure = cedobject_factory.make_procedure(
        ced.root, "Test.TestBuildProcedure.procedure1"
    )
    procedure.add_local_vars(age="Integer")
    # process.add_general_procedure(
    #    "setUp",
    #    parameter="Integer accountId",
    #    local_vars="Integer age, TestEmTaskProcess process",
    #    returns="Integer",
    #    contents="var i=0",
    # )


def assert_file_matches_process(ced, process_path, process):
    loaded_process = ced.open(process_path)
    assert str(loaded_process) == str(process)
