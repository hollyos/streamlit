# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""time_input unit test."""

from datetime import datetime, time, timedelta

from parameterized import parameterized

import streamlit as st
from streamlit.errors import StreamlitAPIException
from streamlit.proto.LabelVisibilityMessage_pb2 import LabelVisibilityMessage
from streamlit.testing.v1.app_test import AppTest
from tests.delta_generator_test_case import DeltaGeneratorTestCase


class TimeInputTest(DeltaGeneratorTestCase):
    """Test ability to marshall time_input protos."""

    def test_just_label(self):
        """Test that it can be called with no value."""
        st.time_input("the label")

        c = self.get_delta_from_queue().new_element.time_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertLessEqual(
            datetime.strptime(c.default, "%H:%M").time(), datetime.now().time()
        )
        self.assertEqual(c.HasField("default"), True)
        self.assertEqual(c.disabled, False)

    def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.time_input("the label", disabled=True)

        c = self.get_delta_from_queue().new_element.time_input
        self.assertEqual(c.disabled, True)

    def test_none_value(self):
        """Test that it can be called with None as initial value."""
        st.time_input("the label", value=None)

        c = self.get_delta_from_queue().new_element.time_input
        self.assertEqual(c.label, "the label")
        # If a proto property is null is not determined by this value,
        # but by the check via the HasField method:
        self.assertEqual(c.default, "")
        self.assertEqual(c.HasField("default"), False)

    @parameterized.expand(
        [(time(8, 45), "08:45"), (datetime(2019, 7, 6, 21, 15), "21:15")]
    )
    def test_value_types(self, arg_value, proto_value):
        """Test that it supports different types of values."""
        st.time_input("the label", arg_value)

        c = self.get_delta_from_queue().new_element.time_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, proto_value)

    def test_inside_column(self):
        """Test that it works correctly inside of a column."""
        col1, col2 = st.columns([3, 2])

        with col1:
            st.time_input("foo")

        all_deltas = self.get_all_deltas_from_queue()

        # 4 elements will be created: 1 horizontal block, 2 columns, 1 widget
        self.assertEqual(len(all_deltas), 4)
        time_input_proto = self.get_delta_from_queue().new_element.time_input

        self.assertEqual(time_input_proto.label, "foo")

    @parameterized.expand(
        [
            ("visible", LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE),
            ("hidden", LabelVisibilityMessage.LabelVisibilityOptions.HIDDEN),
            ("collapsed", LabelVisibilityMessage.LabelVisibilityOptions.COLLAPSED),
        ]
    )
    def test_label_visibility(self, label_visibility_value, proto_value):
        """Test that it can be called with label_visibility param."""
        st.time_input("the label", label_visibility=label_visibility_value)

        c = self.get_delta_from_queue().new_element.time_input
        self.assertEqual(c.label_visibility.value, proto_value)

    def test_label_visibility_wrong_value(self):
        with self.assertRaises(StreamlitAPIException) as e:
            st.time_input("the label", label_visibility="wrong_value")
        self.assertEqual(
            str(e.exception),
            "Unsupported label_visibility option 'wrong_value'. Valid values are "
            "'visible', 'hidden' or 'collapsed'.",
        )

    def test_st_time_input(self):
        """Test st.time_input."""
        value = time(8, 45)
        st.time_input("Set an alarm for", value)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.time_input.default, "08:45")
        self.assertEqual(el.time_input.step, timedelta(minutes=15).seconds)

    def test_st_time_input_with_step(self):
        """Test st.time_input with step."""
        value = time(9, 00)
        st.time_input("Set an alarm for", value, step=timedelta(minutes=5))

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.time_input.default, "09:00")
        self.assertEqual(el.time_input.step, timedelta(minutes=5).seconds)

    def test_st_time_input_exceptions(self):
        """Test st.time_input exceptions."""
        value = time(9, 00)
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=True)
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=(90, 0))
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=1)
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=59)
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=timedelta(hours=24))
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=timedelta(days=1))

    def test_shows_cached_widget_replay_warning(self):
        """Test that a warning is shown when this widget is used inside a cached function."""
        st.cache_data(lambda: st.time_input("the label"))()

        # The widget itself is still created, so we need to go back one element more:
        el = self.get_delta_from_queue(-2).new_element.exception
        self.assertEqual(el.type, "CachedWidgetWarning")
        self.assertTrue(el.is_warning)


def test_time_input_interaction():
    """Test interactions with an empty time_input widget."""

    def script():
        import streamlit as st

        st.time_input("the label", value=None)

    at = AppTest.from_function(script).run()
    time_input = at.time_input[0]
    assert time_input.value is None

    # Input a time:
    at = time_input.set_value(time(8, 45)).run()
    time_input = at.time_input[0]
    assert time_input.value == time(8, 45)

    # # Clear the value
    at = time_input.set_value(None).run()
    time_input = at.time_input[0]
    assert time_input.value is None
