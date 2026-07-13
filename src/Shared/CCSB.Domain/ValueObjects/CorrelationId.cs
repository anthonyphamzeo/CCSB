using System;

namespace CCSB.Domain.ValueObjects
{
    public sealed class CorrelationId
    {
        public CorrelationId(Guid value)
        {
            if (value == Guid.Empty)
            {
                throw new ArgumentException("Correlation id cannot be empty.", nameof(value));
            }

            Value = value;
        }

        public Guid Value { get; }

        public static CorrelationId New() => new CorrelationId(Guid.NewGuid());

        public override string ToString() => Value.ToString("D");
    }
}
