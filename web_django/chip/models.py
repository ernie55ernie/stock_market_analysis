from django.db import models
# Create your models here.

class BrokerData(models.Model):
    key = models.CharField(max_length=60,
                           primary_key=True,
                           help_text="code broker broker_branch YYYY-MM-DD")
    broker = models.CharField(max_length=20, help_text="券商")
    broker_branch = models.CharField(max_length=20, help_text="據點")
    code = models.CharField(max_length=4, help_text="公司代碼")
    date = models.DateField(help_text="日期")
    buy = models.IntegerField(help_text="買進(張)")
    sell = models.IntegerField(help_text="賣出(張)")
    total = models.IntegerField(help_text="買賣總額(張)")
    net = models.IntegerField(help_text="買賣超(張)")

    def __str__(self):
        return f"{self.code} {self.broker} - {self.broker_branch} ({self.date})"

    def save(self, *args, **kwargs):
        # Ensure the composite key is handled automatically
        self.key = f"{self.code} {self.broker} {self.broker_branch} {self.date}"
        super().save(*args, **kwargs)
