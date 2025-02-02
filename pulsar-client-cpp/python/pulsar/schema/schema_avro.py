#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import _pulsar
import io
import enum

from . import Record
from .schema import Schema

try:
    import fastavro

    HAS_AVRO = True
except ModuleNotFoundError:
    HAS_AVRO = False

if HAS_AVRO:

    class AvroSchema(Schema):
        def __init__(self, record_cls):
            super(AvroSchema, self).__init__(record_cls, _pulsar.SchemaType.AVRO, record_cls.schema(), "AVRO")
            self._schema = record_cls.schema()

        def _get_serialized_value(self, x):
            if isinstance(x, enum.Enum):
                return x.name
            elif isinstance(x, Record):
                return self.encode_dict(x.__dict__)
            elif isinstance(x, list):
                arr = []
                for item in x:
                    arr.append(self._get_serialized_value(item))
                return arr
            elif isinstance(x, dict):
                return self.encode_dict(x)
            else:
                return x

        def encode(self, obj):
            self._validate_object_type(obj)
            buffer = io.BytesIO()
            m = self.encode_dict(obj.__dict__)
            fastavro.schemaless_writer(buffer, self._schema, m)
            return buffer.getvalue()

        def encode_dict(self, d):
            obj = {}
            for k, v in d.items():
                obj[k] = self._get_serialized_value(v)
            return obj

        def decode(self, data):
            buffer = io.BytesIO(data)
            d = fastavro.schemaless_reader(buffer, self._schema)
            return self._record_cls(**d)


else:

    class AvroSchema(Schema):
        def __init__(self, _record_cls):
            raise Exception(
                "Avro library support was not found. Make sure to install Pulsar client "
                + "with Avro support: pip3 install 'pulsar-client[avro]'"
            )

        def encode(self, obj):
            pass

        def decode(self, data):
            pass
