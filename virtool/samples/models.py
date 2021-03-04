from sqlalchemy import Column, Integer, String, DateTime

from virtool.postgres import Base


class SampleReadsFile(Base):
    """
    SQL model to store new sample reads files

    """
    __tablename__ = "sample_reads_files"

    id = Column(Integer, primary_key=True)
    sample = Column(String)
    name_on_disk = Column(String)
    paired = Column(Integer)
    size = Column(Integer)
    uploaded_at = Column(DateTime)

    def __repr__(self):
        return f"<SampleReadsFile(id={self.id}, sample={self.sample} name_on_disk={self.name_on_disk}, " \
               f"paired={self.paired}, size={self.size}, uploaded_at={self.uploaded_at})>"