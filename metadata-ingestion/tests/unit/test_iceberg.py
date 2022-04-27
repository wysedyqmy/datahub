from typing import Any

import pytest
from iceberg.api import types as IcebergTypes
from iceberg.api.types.types import NestedField

from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.source.azure.azure_common import AdlsSourceConfig
from datahub.ingestion.source.iceberg import IcebergSource, IcebergSourceConfig
from datahub.metadata.com.linkedin.pegasus2avro.schema import (
    ArrayType,
    MapType,
    SchemaField,
)
from datahub.metadata.schema_classes import (
    ArrayTypeClass,
    BooleanTypeClass,
    BytesTypeClass,
    DateTypeClass,
    FixedTypeClass,
    MapTypeClass,
    NumberTypeClass,
    RecordTypeClass,
    StringTypeClass,
    TimeTypeClass,
)


def iceberg_source() -> IcebergSource:
    adls: AdlsSourceConfig = AdlsSourceConfig(
        account_name="test", container_name="test"
    )
    return IcebergSource(
        ctx=PipelineContext(run_id="iceberg-source-test"),
        config=IcebergSourceConfig(adls=adls),
    )


def assert_field(
    schema_field: SchemaField,
    expected_description: str,
    expected_nullable: bool,
    expected_type: Any,
) -> None:
    assert schema_field.description == expected_description
    assert schema_field.nullable == expected_nullable
    assert isinstance(schema_field.type.type, expected_type)


@pytest.mark.parametrize(
    "iceberg_type, expected_schema_field_type",
    [
        (IcebergTypes.BinaryType.get(), BytesTypeClass),
        (IcebergTypes.BooleanType.get(), BooleanTypeClass),
        (IcebergTypes.DateType.get(), DateTypeClass),
        (
            IcebergTypes.DecimalType.of(3, 2),
            NumberTypeClass,
        ),
        (IcebergTypes.DoubleType.get(), NumberTypeClass),
        (IcebergTypes.FixedType.of_length(4), FixedTypeClass),
        (IcebergTypes.FloatType.get(), NumberTypeClass),
        (IcebergTypes.IntegerType.get(), NumberTypeClass),
        (IcebergTypes.LongType.get(), NumberTypeClass),
        (IcebergTypes.StringType.get(), StringTypeClass),
        (
            IcebergTypes.TimestampType.with_timezone(),
            TimeTypeClass,
        ),
        (
            IcebergTypes.TimestampType.without_timezone(),
            TimeTypeClass,
        ),
        (IcebergTypes.TimeType.get(), TimeTypeClass),
        (
            IcebergTypes.UUIDType.get(),
            StringTypeClass,
        ),  # Is this the right mapping or it should be a FixedType?
    ],
)
def test_iceberg_primitive_type_to_schema_field(
    iceberg_type: IcebergTypes.PrimitiveType, expected_schema_field_type: Any
) -> None:
    """
    Test converting a primitive typed Iceberg field to a SchemaField
    """
    iceberg_source_instance = iceberg_source()
    for column in [
        NestedField.required(
            1, "required_field", iceberg_type, "required field documentation"
        ),
        NestedField.optional(
            1, "optional_field", iceberg_type, "optional field documentation"
        ),
    ]:
        schema_fields = iceberg_source_instance._get_schema_fields_for_column(column)
        assert len(schema_fields) == 1
        assert_field(
            schema_fields[0], column.doc, column.is_optional, expected_schema_field_type
        )


def test_iceberg_list_to_schema_field():
    """
    This test is failing because avro does not keep the nestedType.
    Here is a link to a Slack post that tries to describe the issue:
    https://datahubspace.slack.com/archives/C02SRNN11EG/p1648687685930859?thread_ts=1647388015.115169&cid=C02SRNN11EG
    """
    list_column: NestedField = NestedField.required(
        1,
        "listField",
        IcebergTypes.ListType.of_required(2, IcebergTypes.StringType.get()),
        "documentation",
    )
    iceberg_source_instance = iceberg_source()
    schema_fields = iceberg_source_instance._get_schema_fields_for_column(list_column)
    assert len(schema_fields) == 1
    assert_field(
        schema_fields[0], list_column.doc, list_column.is_optional, ArrayTypeClass
    )
    assert isinstance(schema_fields[0].type.type, ArrayType)
    arrayType: ArrayType = schema_fields[0].type.type
    assert isinstance(arrayType.nestedType, StringTypeClass)


def test_iceberg_map_to_schema_field():
    """
    This test is failing because avro does not keep the nestedType.
    Here is a link to a Slack post that tries to describe the issue:
    https://datahubspace.slack.com/archives/C02SRNN11EG/p1648687685930859?thread_ts=1647388015.115169&cid=C02SRNN11EG
    """
    map_column: NestedField = NestedField.required(
        1,
        "mapField",
        IcebergTypes.MapType.of_required(
            11, 12, IcebergTypes.StringType.get(), IcebergTypes.IntegerType.get()
        ),
        "documentation",
    )
    iceberg_source_instance = iceberg_source()
    schema_fields = iceberg_source_instance._get_schema_fields_for_column(map_column)
    assert len(schema_fields) == 1
    assert_field(schema_fields[0], map_column.doc, map_column.is_optional, MapTypeClass)
    assert isinstance(schema_fields[0].type.type, MapType)
    mapType: MapType = schema_fields[0].type.type
    assert isinstance(mapType.keyType, StringTypeClass)
    assert isinstance(mapType.valueType, NumberTypeClass)


@pytest.mark.parametrize(
    "iceberg_type, expected_schema_field_type",
    [
        (IcebergTypes.BinaryType.get(), BytesTypeClass),
        (IcebergTypes.BooleanType.get(), BooleanTypeClass),
        (IcebergTypes.DateType.get(), DateTypeClass),
        (
            IcebergTypes.DecimalType.of(3, 2),
            NumberTypeClass,
        ),
        (IcebergTypes.DoubleType.get(), NumberTypeClass),
        (IcebergTypes.FixedType.of_length(4), FixedTypeClass),
        (IcebergTypes.FloatType.get(), NumberTypeClass),
        (IcebergTypes.IntegerType.get(), NumberTypeClass),
        (IcebergTypes.LongType.get(), NumberTypeClass),
        (IcebergTypes.StringType.get(), StringTypeClass),
        (
            IcebergTypes.TimestampType.with_timezone(),
            TimeTypeClass,
        ),
        (
            IcebergTypes.TimestampType.without_timezone(),
            TimeTypeClass,
        ),
        (IcebergTypes.TimeType.get(), TimeTypeClass),
        (
            IcebergTypes.UUIDType.get(),
            StringTypeClass,
        ),  # Is this the right mapping or it should be a FixedType?
    ],
)
def test_iceberg_struct_to_schema_field(iceberg_type, expected_schema_field_type):
    field1: NestedField = NestedField.required(
        11, "field1", iceberg_type, "field documentation"
    )
    struct_column: NestedField = NestedField.required(
        1, "structField", IcebergTypes.StructType.of([field1]), "struct documentation"
    )
    iceberg_source_instance = iceberg_source()
    schema_fields = iceberg_source_instance._get_schema_fields_for_column(struct_column)
    assert len(schema_fields) == 2
    assert_field(
        schema_fields[0], struct_column.doc, struct_column.is_optional, RecordTypeClass
    )
    assert_field(
        schema_fields[1], field1.doc, field1.is_optional, expected_schema_field_type
    )


def test_avro_decimal_bytes_nullable():
    """
    The following test exposes a problem with decimal (bytes) not preserving extra attributes like _nullable.  Decimal (fixed) and Boolean for example do.
    NOTE: This bug was by-passed by mapping the Decimal type to fixed instead of bytes.
    """
    import avro.schema

    decimal_avro_schema_string = """{"type": "record", "name": "__struct_", "fields": [{"type": {"type": "bytes", "precision": 3, "scale": 2, "logicalType": "decimal", "native_data_type": "decimal(3, 2)", "_nullable": false}, "name": "required_field", "doc": "required field documentation"}]}"""
    decimal_avro_schema = avro.schema.parse(decimal_avro_schema_string)
    print("\nDecimal (bytes)")
    print(
        f"Original avro schema string:                         {decimal_avro_schema_string}"
    )
    print(f"After avro parsing, _nullable attribute is missing:  {decimal_avro_schema}")

    decimal_fixed_avro_schema_string = """{"type": "record", "name": "__struct_", "fields": [{"type": {"type": "fixed", "logicalType": "decimal", "precision": 3, "scale": 2, "native_data_type": "decimal(3, 2)", "_nullable": false, "name": "bogusName", "size": 16}, "name": "required_field", "doc": "required field documentation"}]}"""
    decimal_fixed_avro_schema = avro.schema.parse(decimal_fixed_avro_schema_string)
    print("\nDecimal (fixed)")
    print(
        f"Original avro schema string:                           {decimal_fixed_avro_schema_string}"
    )
    print(
        f"After avro parsing, _nullable attribute is preserved:  {decimal_fixed_avro_schema}"
    )

    boolean_avro_schema_string = """{"type": "record", "name": "__struct_", "fields": [{"type": {"type": "boolean", "native_data_type": "boolean", "_nullable": false}, "name": "required_field", "doc": "required field documentation"}]}"""
    boolean_avro_schema = avro.schema.parse(boolean_avro_schema_string)
    print("\nBoolean")
    print(
        f"Original avro schema string:                           {boolean_avro_schema_string}"
    )
    print(
        f"After avro parsing, _nullable attribute is preserved:  {boolean_avro_schema}"
    )