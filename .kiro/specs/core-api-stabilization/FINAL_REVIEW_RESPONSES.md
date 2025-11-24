# Final Review Responses

## Review Summary

**Assessment:** Approve with Minor Changes
**Confidence Level:** Medium

## Issues Addressed

### Issue 1: Column Accuracy for Inline Elements (Severity: Minor)

**Concern:** Column recovery is heuristic (block-level only; inline elements inherit block column; multi-line tokens use line length for end_column). This may fall short of Req 3 AC1/AC3/AC5's "exact source location" for inline errors or fine-grained quick-fixes.

**✅ Resolution:**

Added comprehensive documentation section **"Inline Span Accuracy and Acceptance Scope"** that:

1. **Explicitly defines acceptance scope:**

   - Block-level elements: Accurate (headings, lists, code blocks, paragraphs)
   - Inline elements: Inherit parent block's column (bold, links, inline code)
   - Multi-line tokens: Start column only, end column is line length

1. **Clarifies requirement interpretation:**

   - Req 3 AC1 ("exact source location"): Satisfied for block-level elements
   - Req 3 AC3 ("accurate cursor positioning"): LSP positions at block start
   - Req 3 AC5 ("round-trip mapping"): Preserved spans enable block-level mapping

1. **Documents future enhancement path:**

   - Out of scope for this spec
   - Could add lightweight inline lexer pass if needed
   - Would store in `Node.inline_spans: list[InlineSpan]` field

1. **Adds testing strategy:**

   - Unit tests validate block-level column accuracy
   - Integration tests document inline element behavior
   - Performance tests ensure \<5% overhead

**Impact:** Clear expectations set for what "exact source location" means in this spec. Block-level accuracy is sufficient for most LSP features (diagnostics, go-to-definition). Inline precision can be added later if needed.

______________________________________________________________________

### Issue 2: Materialized View to Source Mapping (Severity: Minor)

**Concern:** Req 3 AC5 calls for mapping materialized view positions to source; design preserves original spans but doesn't define how view offsets (post-transform or multi-file compose) map back (no mapping table or projection function).

**✅ Resolution:**

Added comprehensive section **"Materialized View to Source Mapping"** that defines:

1. **Data Structure:**

   ```python
   @dataclass(frozen=True)
   class ViewSourceMapping:
       view_span: SourceSpan      # Position in materialized view
       source_span: SourceSpan    # Position in original source
       node_id: NodeId            # Stable identifier
       transform: str             # e.g., "promoted", "nested"

       def project_to_source(self, view_line: int, view_column: int) -> tuple[str, int, int]:
           """Project view position to source coordinates."""
   ```

1. **Document Integration:**

   ```python
   class Document:
       _view_mappings: list[ViewSourceMapping]

       def find_source_position(self, view_line: int, view_column: int) -> tuple[str, int, int] | None:
           """Find source position for given view position."""
   ```

1. **When Mappings Are Created:**

   - During parsing: Identity mappings (view = source)
   - During transformations: Operations create new mappings
   - During multi-file composition: Mappings track file origins

1. **LSP Integration Example:**

   - Shows how diagnostics use mappings to report correct source locations
   - Handles fallback when mapping not found

1. **Scope Clarification:**

   - ✅ In Scope: Basic infrastructure, identity mappings, preserved spans
   - ⚠️ Partial Scope: Mapping updates during operations
   - ❌ Out of Scope: Multi-file composition (deferred to Spec 2)

1. **Testing Strategy:**

   - Unit tests for `project_to_source()` with various configurations
   - Integration tests verify mappings after transformations
   - LSP tests verify correct source reporting

1. **Performance Considerations:**

   - O(n) lookup (acceptable for typical documents)
   - Future optimization: spatial index if needed
   - ~64 bytes per mapping (low memory overhead)

**Impact:** Clear specification of how view-to-source mapping works. Provides concrete API for LSP integration. Scopes work appropriately (basic infrastructure in this spec, advanced features in Spec 2).

______________________________________________________________________

## Open Questions - Answered

### Q1: Do we plan to add an inline-level lexer/pass for precise column/end_column, or is block-level accuracy sufficient?

**Answer:** Block-level accuracy is sufficient for this spec's acceptance criteria. Inline-level precision is documented as a future enhancement (out of scope) that can be added if LSP features require it. Testing strategy will validate block-level accuracy and document inline behavior.

### Q2: How will materialized view offsets be mapped back to SourceSpan (data structure/API)? Is a provenance table planned in this slice or deferred?

**Answer:**

- **Data structure:** `ViewSourceMapping` class with `project_to_source()` method
- **API:** `Document.find_source_position(view_line, view_column)` for lookup
- **Scope:** Basic infrastructure and identity mappings in this spec; complex multi-file mappings deferred to Spec 2
- **Storage:** `Document._view_mappings: list[ViewSourceMapping]` (simple list, O(n) lookup)

______________________________________________________________________

## Requirements Coverage - Updated

| Requirement | Status | Notes |
|-------------|--------|-------|
| Req 1: Stable Node Identity | ✅ | Canonicalization, caching, provenance, dual-ID serialization |
| Req 2: Internal Operations | ✅ | Internal ops return Documents; bridge thin; spans preserved |
| Req 3: Source Position Tracking | ✅ | Block-level accuracy documented; view→source mapping specified |
| Req 4: Metadata Immutability | ✅ | Deep-copy with optional persistent structures |
| Req 5: API Paradigm Unification | ✅ | by_id bridge and delegation |
| Req 6: Type Safety | ✅ | TypeGuards + Visitor; mypy/pyright |
| Req 7: Compatibility | ✅ | 3-release timeline with dual-IDs |
| Req 8: Performance | ✅ | Representative corpus benchmarks, 2x target |
| Req 9: Operation Registry | ✅ | Decorator-based auto-registration |
| Req 10: Diagnostics | ✅ | Structured diagnostics with spans |

______________________________________________________________________

## Final Status

**All review concerns addressed:**

- ✅ Inline span accuracy scope explicitly documented
- ✅ View-to-source mapping data structure and API specified
- ✅ Testing strategies defined for both concerns
- ✅ Scope boundaries clarified (what's in/out of this spec)
- ✅ Future enhancement paths documented

**Design Quality:**

- Maintains "Approve with Minor Changes" status
- All technical concerns resolved with concrete specifications
- Clear acceptance criteria for block-level accuracy
- Practical approach to view mapping (basic infrastructure now, advanced features later)

**Ready for:** Final approval and implementation

______________________________________________________________________

## Changes Made to Design Document

### Section Added: "Inline Span Accuracy and Acceptance Scope"

**Location:** After "Multi-File Span Mapping" section

**Content:**

- Defines block-level vs inline-level accuracy
- Clarifies requirement interpretation
- Documents future enhancement path
- Specifies testing strategy

### Section Added: "Materialized View to Source Mapping"

**Location:** After "Inline Span Accuracy" section

**Content:**

- `ViewSourceMapping` data structure
- `Document._view_mappings` integration
- When mappings are created
- LSP integration example
- Scope clarification (in/out of this spec)
- Testing strategy
- Performance considerations

**Total Addition:** ~200 lines of detailed specification addressing both review concerns
