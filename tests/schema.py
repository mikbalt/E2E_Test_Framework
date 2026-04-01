"""
Schema definition for validating TestHSM CLI configuration files.

Supports:
- Nested structure validation
- Type checking
- Allowed values enforcement
"""

class BaseSchema:
    """Base schema with common validation structure."""

    @classmethod
    def get_schema(cls):
        """Return schema dictionary."""
        raise NotImplementedError("Schema must implement get_schema()")

# -------------------------------------------------
# HL (High Level) Schema
# -------------------------------------------------
class TestHsmConfigSchemaHL(BaseSchema):
    """Schema for HL (High Level) TestHSM configuration."""

    @classmethod
    def get_schema(cls):
        return {
            "hsm": {
                "supplier": {
                    "required": True,
                    "type": str,
                    "allowed": ["Rooky"]
                },
                "type": {
                    "required": True,
                    "type": str,
                    "allowed": ["Card"]
                },
                "mode": {
                    "required": True,
                    "type": str,
                    "allowed": ["ClientServer"]
                },
                "dll": {
                    "required": True,
                    "type": str,
                    "allowed": ["CPSInterface"]
                },
                "coprocessor_number": {
                    "type": int
                },
        
                # Nested config
                "config": {
                    "fips": {
                        "type": bool
                    },
                    "firmware": {
                        "type": str,
                        "allowed": ["All", "FW2_08", "FW3_20_10", "FW5_06_02", "SDK4_32"]
                    }
                }
            },
        
            # -------------------------------------------------
            # Network
            # -------------------------------------------------
            "network": {
                "dphsm_ip": {
                    "type": str,
                },
                "dphsm_port": {
                    "type": int
                },
                "receive_timeout_ms": {
                    "type": int
                }
            },
        
            # -------------------------------------------------
            # Test Execution
            # -------------------------------------------------
            "test": {
                "working_directory": {
                    "required": True,
                    "type": str,
                    "allowed": ["C:\\Users\\Administrator\\Documents\\HSM-Tools\\Test Folder\\Test4\\ROOKY_FIPS_2021\\UnitTest_HSMRookyApplet\\general\\CommonFile\\CPSDLL\\TM_CPS_ORG_002"]
                },
                "file_filter": {
                    "type": str,
                    "allowed": ["BasicFct","CosmopolIC","GSM"]
                },
                "description_filter": {
                    "type": str
                },
                "scripts": {
                    "type": list
                },
                "exclude_pinpad": {
                    "type": bool
                },
                "repeat": {
                    "type": int
                },
                "auto_configure": {
                    "type": bool
                }
            },
        
            # -------------------------------------------------
            # Performance
            # -------------------------------------------------
            "performance": {
                "global_stats": {
                    "type": bool
                },
                "per_test_stats": {
                    "type": bool
                }
            },
        
            # -------------------------------------------------
            # Logging
            # -------------------------------------------------
            "logging": {
                "display_frame": {
                    "type": str,
                    "allowed": ["None", "Always", "OnError"]
                },
                "trace_cps": {
                    "type": bool
                },
                "verbosity": {
                    "type": str,
                    "allowed": ["quiet", "normal", "verbose"]
                }
            },
        
            # -------------------------------------------------
            # Reporting
            # -------------------------------------------------
            "reporting": {
                "format": {
                    "type": str,
                    "allowed": ["junit", "text", "both"]
                },
                "output_directory": {
                    "type": str
                }
            },
        
            # -------------------------------------------------
            # Shim
            # -------------------------------------------------
            "shim": {
                "enabled": {
                    "type": bool
                },
                "mode": {
                    "type": str,
                    "allowed": ["record", "replay"]
                },
                "fixtures_directory": {
                    "type": str
                }
            },
        
            # -------------------------------------------------
            # Activity Log
            # -------------------------------------------------
            "activity_log": {
                "enabled": {
                    "type": bool
                },
                "path": {
                    "type": str
                }
            },
        
            # -------------------------------------------------
            # DP HSM Service
            # -------------------------------------------------
            "dphsm_service": {
                "auto_manage": {
                    "type": bool
                },
                "service_name": {
                    "type": str
                },
                "start_timeout_s": {
                    "type": int
                },
                "stop_timeout_s": {
                    "type": int
                },
                "console_path": {
                    "type": str
                }
            }                
        }

# -------------------------------------------------
# DP Schema
# -------------------------------------------------
class TestHsmConfigSchemaDP(BaseSchema):
    """Schema for DP (Data Preparation / DPHSM) configuration."""

    @classmethod
    def get_schema(cls):
        return {
            "hsm": {
                "supplier": {
                    "required": True,
                    "type": str,
                    "allowed": ["Rooky"]
                },
                "type": {
                    "required": True,
                    "type": str,
                    "allowed": ["Card"]
                },
                "mode": {
                    "required": True,
                    "type": str,
                    "allowed": ["ClientServer"]
                },
                "dll": {
                    "required": True,
                    "type": str,
                    "allowed": ["Dphsm"]
                },
                "coprocessor_number": {
                    "type": int
                },
        
                # Nested config
                "config": {
                    "fips": {
                        "type": bool
                    },
                    "firmware": {
                        "type": str,
                        "allowed": ["All", "FW2_08", "FW3_20_10", "FW5_06_02", "SDK4_32"]
                    }
                }
            },
        
            # -------------------------------------------------
            # Network
            # -------------------------------------------------
            "network": {
                "dphsm_ip": {
                    "type": str,
                    "allowed": ["127.0.0.1"]
                },
                "dphsm_port": {
                    "type": int,
                     "allowed": [52003]
                },
                "receive_timeout_ms": {
                    "type": int
                }
            },
        
            # -------------------------------------------------
            # Test Execution
            # -------------------------------------------------
            "test": {
                "working_directory": {
                    "required": True,
                    "type": str,
                    "allowed": ["C:\\Users\\Administrator\\Documents\\HSM-Tools\\Test Folder\\Test4\\ROOKY_FIPS_2021\\UnitTest_HSMRookyApplet\\general\\CommonFile\\DP_HSM\\TM_CPS_ORG_003"]
                },
                "file_filter": {
                    "type": str,
                    "allowed": ["I010"]
                },
                "description_filter": {
                    "type": str
                },
                "scripts": {
                    "type": list
                },
                "exclude_pinpad": {
                    "type": bool
                },
                "repeat": {
                    "type": int
                },
                "auto_configure": {
                    "type": bool
                }
            },
        
            # -------------------------------------------------
            # Performance
            # -------------------------------------------------
            "performance": {
                "global_stats": {
                    "type": bool
                },
                "per_test_stats": {
                    "type": bool
                }
            },
        
            # -------------------------------------------------
            # Logging
            # -------------------------------------------------
            "logging": {
                "display_frame": {
                    "type": str,
                    "allowed": ["None", "Always", "OnError"]
                },
                "trace_cps": {
                    "type": bool
                },
                "verbosity": {
                    "type": str,
                    "allowed": ["quiet", "normal", "verbose"]
                }
            },
        
            # -------------------------------------------------
            # Reporting
            # -------------------------------------------------
            "reporting": {
                "format": {
                    "type": str,
                    "allowed": ["junit", "text", "both"]
                },
                "output_directory": {
                    "type": str
                }
            },
        
            # -------------------------------------------------
            # Shim
            # -------------------------------------------------
            "shim": {
                "enabled": {
                    "type": bool
                },
                "mode": {
                    "type": str,
                    "allowed": ["record", "replay"]
                },
                "fixtures_directory": {
                    "type": str
                }
            },
        
            # -------------------------------------------------
            # Activity Log
            # -------------------------------------------------
            "activity_log": {
                "enabled": {
                    "type": bool
                },
                "path": {
                    "type": str
                }
            },
        
            # -------------------------------------------------
            # DP HSM Service
            # -------------------------------------------------
            "dphsm_service": {
                "auto_manage": {
                    "type": bool
                },
                "service_name": {
                    "type": str
                },
                "start_timeout_s": {
                    "type": int
                },
                "stop_timeout_s": {
                    "type": int
                },
                "console_path": {
                    "type": str
                }
            }                
        }            