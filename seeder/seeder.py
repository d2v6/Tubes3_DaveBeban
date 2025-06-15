import os
import sys
import re
from mysql.connector import Error
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection
from src.utils.encryption import FieldEncryption

load_dotenv()


class SQLSeeder:
    """Seeder that reads and executes SQL data from file"""

    def __init__(self):
        self.db = DatabaseConnection()
        self.field_encryption = FieldEncryption()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.sql_file_path = os.path.join(base_dir, "tubes3_seeding.sql")

    def connect_and_seed(self):
        """Main method to connect and seed database"""
        print("SQL DATABASE SEEDER")
        print("=" * 50)

        try:
            # Connect to database
            if not self.db.connect():
                print("❌ Failed to connect to database")
                return False

            print("✅ Connected to database successfully")

            # Read and execute SQL file
            if self.execute_sql_file():
                print("✅ Database seeding completed successfully!")
                return True
            else:
                print("❌ Database seeding failed!")
                return False

        except Exception as e:
            print(f"❌ Seeding error: {e}")
            return False
        finally:
            self.db.disconnect()

    def execute_sql_file(self):
        """Read and execute SQL commands from file"""
        try:
            # Check if SQL file exists
            if not os.path.exists(self.sql_file_path):
                print(f"❌ SQL file not found: {self.sql_file_path}")
                return False

            # Read SQL file
            with open(self.sql_file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()

            # Split SQL commands (basic splitting by semicolon)
            sql_commands = [cmd.strip()
                            for cmd in sql_content.split(';') if cmd.strip()]

            # Execute each command
            executed_count = 0
            for i, command in enumerate(sql_commands, 1):
                try:
                    # Skip comments and empty lines
                    if command.startswith('--') or command.startswith('/*') or not command:
                        continue
                    self._execute_command(command)
                    executed_count += 1

                except Error as e:
                    print(f"❌ Error executing command {i}: {e}")
                    return False
                except Exception as e:
                    print(f"❌ Unexpected error in command {i}: {e}")
                    return False

            print(f"✅ Successfully executed {executed_count} SQL commands")

            # Verify the seeding
            self._verify_seeding()

            return True

        except Exception as e:
            print(f"❌ Error reading/executing SQL file: {e}")
            return False

    def _execute_command(self, command):
        """Execute a single SQL command"""
        # Check if this is an ApplicantProfile INSERT command
        print(f"Executing command: {command[:50]}...")  # Log first 50 chars
        if re.search(r'INSERT\s+INTO\s+ApplicantProfile', command, re.IGNORECASE):
            command = self._process_applicant_profile_insert(command)

        if command.upper().startswith('SELECT'):
            return self.db.execute_query(command)
        else:
            return self.db.execute_update(command)

    def _extract_table_name(self, create_command):
        """Extract table name from CREATE TABLE command"""
        try:
            parts = create_command.split()
            table_index = parts.index('TABLE') + 1
            if table_index < len(parts):
                table_name = parts[table_index]
                return table_name.replace('IF', '').replace('NOT', '').replace('EXISTS', '').strip()
            return "Unknown"
        except:
            return "Unknown"

    def _extract_insert_table_name(self, insert_command):
        """Extract table name from INSERT command"""
        try:
            parts = insert_command.split()
            into_index = parts.index('INTO') + 1
            if into_index < len(parts):
                table_name = parts[into_index]
                return table_name.strip('()')
            return "Unknown"
        except:
            return "Unknown"

    def _count_insert_records(self, insert_command):
        """Count number of records in INSERT command"""
        try:
            # Count the number of VALUE tuples
            values_part = insert_command.split(
                'VALUES', 1)[1] if 'VALUES' in insert_command else ""
            # Simple count of opening parentheses after VALUES
            # Subtract nested parentheses
            return values_part.count('(') - values_part.count('((')
        except:
            return "Unknown"

    def _verify_seeding(self):
        """Verify that data was seeded correctly"""
        try:
            # Check ApplicantProfile table
            profile_count = self.db.execute_query(
                "SELECT COUNT(*) as count FROM ApplicantProfile")
            if profile_count:
                print(
                    # Check ApplicationDetail table
                    f"   ApplicantProfile: {profile_count[0]['count']} records")
            detail_count = self.db.execute_query(
                "SELECT COUNT(*) as count FROM ApplicationDetail")
            if detail_count:
                print(
                    f"   ApplicationDetail: {detail_count[0]['count']} records")

            # Check sample encrypted data
            sample_profiles = self.db.execute_query(
                "SELECT applicant_id, first_name, last_name, date_of_birth FROM ApplicantProfile LIMIT 5")
            if sample_profiles:
                print("   Sample encrypted profiles:")
                for profile in sample_profiles:
                    # Decrypt only the encrypted fields for verification display
                    try:
                        # Use the existing decrypt method on individual fields
                        decrypted_first_name = self.field_encryption.encryptor.decrypt_data(
                            profile['first_name'])
                        decrypted_last_name = self.field_encryption.encryptor.decrypt_data(
                            profile['last_name'])
                        print(
                            f"      • ID: {profile['applicant_id']} | {decrypted_first_name} {decrypted_last_name} | DOB: {profile['date_of_birth']} (selective encryption)")
                    except Exception as e:
                        print(
                            f"      • Error decrypting profile {profile['applicant_id']}: {e}")

            print("✅ Data verification completed!")

        except Exception as e:
            print(f"Verification error: {e}")

    def _process_applicant_profile_insert(self, command):
        """Process ApplicantProfile INSERT command and encrypt sensitive fields"""
        try:
            print("🔒 Processing ApplicantProfile data with encryption...")

            # Extract the VALUES portion
            values_match = re.search(
                r'VALUES\s*(.+)', command, re.DOTALL | re.IGNORECASE)
            if not values_match:
                return command

            values_part = values_match.group(1)

            # Find all value tuples using regex
            # This matches (value1, 'value2', value3, ...) patterns
            tuple_pattern = r'\(([^)]*(?:\([^)]*\)[^)]*)*)\)'
            tuples = re.findall(tuple_pattern, values_part)

            encrypted_tuples = []

            for i, tuple_content in enumerate(tuples):
                # Parse individual values from the tuple
                # Split by comma but respect quotes
                # Expected: id, first_name, last_name, date_of_birth, address, phone_number
                values = self._parse_tuple_values(tuple_content)
                if len(values) >= 6:
                    # Create profile data dict
                    profile_data = {
                        'applicant_id': values[0].strip().strip("'\""),
                        'first_name': values[1].strip().strip("'\""),
                        'last_name': values[2].strip().strip("'\""),
                        'date_of_birth': values[3].strip().strip("'\""),
                        'address': values[4].strip().strip("'\""),
                        'phone_number': values[5].strip().strip("'\"")
                    }

                    print(
                        # Encrypt only the sensitive fields using the existing encryption method
                        f"   Processing record {i+1}: {profile_data['first_name']} {profile_data['last_name']}")
                    # First, encrypt the profile data
                    encrypted_profile = self.field_encryption.encrypt_profile_data(
                        profile_data)

                    # Then selectively keep non-encrypted fields
                    encrypted_data = {
                        # Keep as-is for foreign key integrity
                        'applicant_id': profile_data['applicant_id'],
                        # Encrypted
                        'first_name': encrypted_profile['first_name'],
                        # Encrypted
                        'last_name': encrypted_profile['last_name'],
                        # Keep as-is for DATE type
                        'date_of_birth': profile_data['date_of_birth'],
                        # Encrypted
                        'address': encrypted_profile['address'],
                        # Encrypted
                        'phone_number': encrypted_profile['phone_number']
                    }

                    # Reconstruct the tuple with encrypted values
                    encrypted_tuple = (
                        f"('{encrypted_data['applicant_id']}', "
                        f"'{encrypted_data['first_name']}', "
                        f"'{encrypted_data['last_name']}', "
                        f"'{encrypted_data['date_of_birth']}', "
                        f"'{encrypted_data['address']}', "
                        f"'{encrypted_data['phone_number']}')"
                    )
                    encrypted_tuples.append(encrypted_tuple)
                else:
                    print(
                        f"   ⚠️  Skipping malformed tuple: {tuple_content}")
                    encrypted_tuples.append(f"({tuple_content})")

            # Reconstruct the command with encrypted data
            base_command = command[:values_match.start(1)]
            encrypted_command = base_command + \
                ',\n'.join(encrypted_tuples) + ';'

            print(
                f"✅ Encrypted {len(encrypted_tuples)} ApplicantProfile records")
            return encrypted_command

        except Exception as e:
            print(
                f"❌ Error processing ApplicantProfile encryption: {e}")
            return command

    def _parse_tuple_values(self, tuple_content):
        """Parse individual values from a tuple string, respecting quotes"""
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None

        i = 0
        while i < len(tuple_content):
            char = tuple_content[i]

            if not in_quotes and char in ["'", '"']:
                in_quotes = True
                quote_char = char
                current_value += char
            elif in_quotes and char == quote_char:
                # Check if it's an escaped quote
                if i + 1 < len(tuple_content) and tuple_content[i + 1] == quote_char:
                    current_value += char + char
                    i += 1  # Skip the next quote
                else:
                    in_quotes = False
                    quote_char = None
                    current_value += char
            elif not in_quotes and char == ',':
                values.append(current_value.strip())
                current_value = ""
            else:
                current_value += char

            i += 1

        # Add the last value
        if current_value.strip():
            values.append(current_value.strip())

        return values


def main():
    """Run the SQL seeder"""
    seeder = SQLSeeder()
    success = seeder.connect_and_seed()

    if success:
        print("\n✅ SQL seeding completed successfully!")
        print(" You can now run your CV ATS application with the seeded data")
    else:
        print("\n❌ SQL seeding failed!")
        print(" Check the error messages above and your database configuration")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
