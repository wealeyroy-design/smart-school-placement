import { useAuth } from "../../auth/AuthContext";
import ParentView from "./ParentView";
import StudentSelfView from "./StudentSelfView";

export default function StudentPortal() {
  const { user } = useAuth();
  return user.role === "parent" ? <ParentView /> : <StudentSelfView />;
}
