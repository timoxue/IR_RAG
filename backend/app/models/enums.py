from enum import Enum


class Role(str, Enum):
	IR = "IR"
	REVIEWER = "REVIEWER"
	ADMIN = "ADMIN"


class DocCategory(str, Enum):
	ANNOUNCEMENT = "announcement"  # 公告
	RESEARCH = "research"          # 研报/研发
	FAQ = "faq"
	POLICY = "policy"              # 政策法规
	DISCLOSURE = "disclosure"      # 对外披露材料


class ReviewStatus(str, Enum):
	PENDING = "pending"
	NEEDS_REVISION = "needs_revision"
	APPROVED = "approved"
	REJECTED = "rejected"


class ImportStatus(str, Enum):
	QUEUED = "queued"
	PROCESSING = "processing"
	COMPLETED = "completed"
	FAILED = "failed"
