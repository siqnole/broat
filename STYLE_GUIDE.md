# Bronx Bot Style Guide

This document defines the visual styling guidelines for Bronx bot responses, embeds, and messages.

## Color Palette

Use soft, cold colors for a cohesive and calming aesthetic.

### Primary Colors

| Color Name | Hex Code | Usage |
|-----------|----------|-------|
| **Sky Blue** | `#5BA4E8` | General info, neutral embeds |
| **Soft Purple** | `#9B7EED` | Help commands, documentation |
| **Lavender** | `#B4A7D6` | User information, profiles |
| **Periwinkle** | `#8DA3E8` | Server information |

### Success & Positive

| Color Name | Hex Code | Usage |
|-----------|----------|-------|
| **Mint** | `#7DD3C0` | Success messages, confirmations |
| **Light Teal** | `#5FCFC4` | Completed actions |
| **Soft Cyan** | `#6BB6D6` | Positive feedback |

### Warning & Error

| Color Name | Hex Code | Usage |
|-----------|----------|-------|
| **Coral** | `#FF8B7A` | Warning messages, caution |
| **Salmon** | `#FF9E8A` | Moderate warnings |
| **Soft Red** | `#F47A7A` | Error messages, failures |
| **Light Rose** | `#E88D9C` | Soft errors, permission denials |

### Accent Colors

| Color Name | Hex Code | Usage |
|-----------|----------|-------|
| **Soft Pink** | `#E6A4B4` | Fun commands, entertainment |
| **Pale Magenta** | `#D896C9` | Special events, highlights |
| **Ice Blue** | `#A8D8EA` | Cool-toned accents |

## Custom Emojis

### Status Emojis

Use these custom emoji IDs for consistent status indicators:

```python
# In your code
EMOJI_YES = "01KK7EC8VP8CMKZW8SB64TCVTC"
EMOJI_NO = "01KK7ECH9ES9SRSB9REFGKZMFB"
EMOJI_WARNING = "01KK7ECQ187S2FZ2X3JS65R9PW"
```

**In messages:**
- ✅ Success/Yes: `:01KK7EC8VP8CMKZW8SB64TCVTC:`
- ❌ Failure/No: `:01KK7ECH9ES9SRSB9REFGKZMFB:`
- ⚠️ Warning: `:01KK7ECQ187S2FZ2X3JS65R9PW:`

### Usage Examples

```python
# Success message
await ctx.send(f":01KK7EC8VP8CMKZW8SB64TCVTC: Command executed successfully!")

# Error message
embed = stoat.SendableEmbed(
    title=":01KK7ECH9ES9SRSB9REFGKZMFB: Error",
    description="Something went wrong.",
    color="#F47A7A"
)

# Warning message
embed = stoat.SendableEmbed(
    title=":01KK7ECQ187S2FZ2X3JS65R9PW: Warning",
    description="Are you sure you want to do this?",
    color="#FF8B7A"
)
```

## Embed Guidelines

### Structure

All embeds should follow this structure:

```python
embed = stoat.SendableEmbed(
    title="Clear, Concise Title",
    description="Detailed information here.\n\nUse line breaks for readability.",
    color="#5BA4E8",  # Choose appropriate color from palette
    icon_url="https://..."  # Optional: relevant icon
)
```

### Title Formatting

- **Do:** Use clear, descriptive titles
- **Do:** Include relevant emoji at the start when appropriate
- **Don't:** Use ALL CAPS (except for emphasis on single words)
- **Don't:** Make titles longer than ~50 characters

**Good Examples:**
- `"User Info — css"`
- `":01KK7EC8VP8CMKZW8SB64TCVTC: Member Kicked"`
- `"Help — General Commands"`

**Bad Examples:**
- `"USER INFORMATION FOR CSS"` (too loud)
- `"Info"` (too vague)
- `"This is all the information about the user you requested"` (too long)

### Description Formatting

Use markdown formatting for clarity:

```markdown
**Bold** for labels and emphasis
`Code blocks` for IDs, commands, filenames
*Italic* for notes and secondary information

Use bullet points:
• Option one
• Option two
• Option three

Or numbered lists:
1. First step
2. Second step
3. Third step
```

### Color Usage by Command Type

| Command Type | Recommended Color | Hex Code |
|-------------|-------------------|----------|
| Help/Info | Soft Purple | `#9B7EED` |
| User Info | Lavender | `#B4A7D6` |
| Server Info | Periwinkle | `#8DA3E8` |
| Success | Mint | `#7DD3C0` |
| Fun/Games | Soft Pink | `#E6A4B4` |
| Moderation | Sky Blue | `#5BA4E8` |
| Warning | Coral | `#FF8B7A` |
| Error | Soft Red | `#F47A7A` |

## Response Patterns

### Success Responses

```python
# Short success
await ctx.send(f":01KK7EC8VP8CMKZW8SB64TCVTC: Done!")

# Detailed success with embed
embed = stoat.SendableEmbed(
    title=":01KK7EC8VP8CMKZW8SB64TCVTC: Action Completed",
    description="Your action was successful.\n\n**Details:** ...",
    color="#7DD3C0"
)
await ctx.send(embeds=[embed])
```

### Error Responses

```python
# Short error
await ctx.send(f":01KK7ECH9ES9SRSB9REFGKZMFB: **Error:** Something went wrong.")

# Detailed error with embed
embed = stoat.SendableEmbed(
    title=":01KK7ECH9ES9SRSB9REFGKZMFB: Error",
    description="**What went wrong:** ...\n\n**How to fix:** ...",
    color="#F47A7A"
)
await ctx.send(embeds=[embed])
```

### Warning Responses

```python
embed = stoat.SendableEmbed(
    title=":01KK7ECQ187S2FZ2X3JS65R9PW: Warning",
    description="This action is **potentially dangerous**.\n\nProceed with caution.",
    color="#FF8B7A"
)
await ctx.send(embeds=[embed])
```

### Info Responses

```python
embed = stoat.SendableEmbed(
    title="Information",
    description="Here's what you need to know:\n\n**Detail 1:** ...\n**Detail 2:** ...",
    color="#5BA4E8"
)
await ctx.send(embeds=[embed])
```

## Consistency Rules

1. **Always use custom emojis** for yes/no/warning instead of unicode emojis
2. **Pick one color per embed** from the style guide
3. **Use bold markdown** for field labels (e.g., `**ID:** 123`)
4. **Include helpful context** in error messages
5. **Keep descriptions scannable** with line breaks and formatting
6. **Be concise** — users should understand at a glance

## Quick Reference

### Common Color Choices

```python
# Copy these into your code
COLOR_INFO = "#5BA4E8"        # General information
COLOR_HELP = "#9B7EED"        # Help commands
COLOR_SUCCESS = "#7DD3C0"     # Success messages
COLOR_WARNING = "#FF8B7A"     # Warnings
COLOR_ERROR = "#F47A7A"       # Errors
COLOR_FUN = "#E6A4B4"         # Fun/entertainment
COLOR_USER = "#B4A7D6"        # User information
COLOR_SERVER = "#8DA3E8"      # Server information
```

### Emoji Constants

```python
# Copy these into your code
EMOJI_YES = "01KK7EC8VP8CMKZW8SB64TCVTC"
EMOJI_NO = "01KK7ECH9ES9SRSB9REFGKZMFB"
EMOJI_WARNING = "01KK7ECQ187S2FZ2X3JS65R9PW"
```

---

*This style guide ensures Bronx maintains a consistent, professional, and visually appealing presence across all commands and responses.*
