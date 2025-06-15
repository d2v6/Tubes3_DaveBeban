from src.database.connection import DatabaseConnection
import os
import sys
from mysql.connector import Error
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


load_dotenv()


class SQLSeeder:
    """Seeder that reads and executes SQL data from file"""

    def __init__(self):
        self.db = DatabaseConnection()
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
                    f"   ApplicantProfile: {profile_count[0]['count']} records")

            # Check ApplicationDetail table
            detail_count = self.db.execute_query(
                "SELECT COUNT(*) as count FROM ApplicationDetail")
            if detail_count:
                print(
                    f"   ApplicationDetail: {detail_count[0]['count']} records")

            # Check sample data
            sample_profiles = self.db.execute_query(
                "SELECT first_name, last_name FROM ApplicantProfile LIMIT 5")
            if sample_profiles:
                print("   Sample profiles:")
                for profile in sample_profiles:
                    print(
                        f"      • {profile['first_name']} {profile['last_name']}")

            print("✅ Data verification completed!")

        except Exception as e:
            print(f"Verification error: {e}")


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
