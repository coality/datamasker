"""Tests for the models module."""

import pytest

from app.models import FunctionalConfig, MaskingRule, ConnectionConfig


class TestMaskingRule:
    """Tests for MaskingRule model."""

    def test_masking_rule_creation(self):
        """Test creating a MaskingRule instance."""
        rule = MaskingRule(
            schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
        )
        assert rule.schema == "dbo"
        assert rule.table == "Personnel"
        assert rule.column == "LastName"
        assert rule.order_by == "PersonID"

    def test_masking_rule_is_frozen(self):
        """Test that MaskingRule is immutable (frozen)."""
        rule = MaskingRule(
            schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
        )
        with pytest.raises(AttributeError):
            rule.schema = "other"

    def test_masking_rule_equality(self):
        """Test MaskingRule equality comparison."""
        rule1 = MaskingRule(
            schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
        )
        rule2 = MaskingRule(
            schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
        )
        rule3 = MaskingRule(
            schema="dbo", table="Personnel", column="FirstName", order_by="PersonID"
        )

        assert rule1 == rule2
        assert rule1 != rule3


class TestFunctionalConfig:
    """Tests for FunctionalConfig model."""

    def test_functional_config_creation(self):
        """Test creating a FunctionalConfig instance."""
        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )
        assert config.masking_format == "<{column}_{counter}>"
        assert config.pad_length == 4
        assert len(config.masking_rules) == 1

    def test_functional_config_pad_length_positive(self):
        """Test pad_length_strictly_positive property."""
        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config_positive = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )
        assert config_positive.pad_length_strictly_positive is True

        config_zero = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=0, masking_rules=rules
        )
        assert config_zero.pad_length_strictly_positive is False

        config_negative = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=-1, masking_rules=rules
        )
        assert config_negative.pad_length_strictly_positive is False

    def test_functional_config_is_frozen(self):
        """Test that FunctionalConfig is immutable (frozen)."""
        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )
        with pytest.raises(AttributeError):
            config.pad_length = 5

    def test_functional_config_empty_rules(self):
        """Test FunctionalConfig with empty rules list."""
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=[]
        )
        assert len(config.masking_rules) == 0


class TestConnectionConfig:
    """Tests for ConnectionConfig model."""

    def test_connection_config_creation(self):
        """Test creating a ConnectionConfig instance."""
        config = ConnectionConfig(
            server="SQL01",
            database="MyDb",
            username="masking_user",
            password_file="secrets/sql-password.dpapi",
        )
        assert config.server == "SQL01"
        assert config.database == "MyDb"
        assert config.username == "masking_user"
        assert config.password_file == "secrets/sql-password.dpapi"

    def test_connection_config_password_file_path(self):
        """Test password_file_path property returns PurePath."""
        config = ConnectionConfig(
            server="SQL01",
            database="MyDb",
            username="masking_user",
            password_file="secrets/sql-password.dpapi",
        )
        from pathlib import PurePath

        p = config.password_file_path
        assert isinstance(p, PurePath)
        assert str(p) == "secrets/sql-password.dpapi"

    def test_connection_config_is_frozen(self):
        """Test that ConnectionConfig is immutable (frozen)."""
        config = ConnectionConfig(
            server="SQL01",
            database="MyDb",
            username="masking_user",
            password_file="secrets/sql-password.dpapi",
        )
        with pytest.raises(AttributeError):
            config.server = "OtherServer"

    def test_connection_config_equality(self):
        """Test ConnectionConfig equality comparison."""
        config1 = ConnectionConfig(
            server="SQL01", database="MyDb", username="user", password_file="path.dpapi"
        )
        config2 = ConnectionConfig(
            server="SQL01", database="MyDb", username="user", password_file="path.dpapi"
        )
        config3 = ConnectionConfig(
            server="SQL02", database="MyDb", username="user", password_file="path.dpapi"
        )

        assert config1 == config2
        assert config1 != config3
